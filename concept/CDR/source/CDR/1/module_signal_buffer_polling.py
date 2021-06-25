#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2018-06-19

import argparse, os, wave, sys
import cPickle as pickle
import pyaudio
import numpy as np

from signal_buffer import SignalBuffer

class Format(object):
    def __init__(self, format_str):
        if format_str == "Int8":
            self._type = np.int8
            self._size = 1
            self._normalization_constant = 2.0**7
        elif format_str == "UInt8":
            self._type = np.uint8
            self._size = 1
            self._normalization_constant = 2.0**8
        elif format_str == "Int16":
            self._type = np.int16
            self._size = 2
            self._normalization_constant = 2.0**15
        # TODO
        #elif format_str == "Int24":
        #    self._type = np.int24
        #    self._size = 3
        #    self._normalization_constant = 2.0**23
        elif format_str == "Int32":
            self._type = np.int32
            self._size = 4
            self._normalization_constant = 2.0**31
        elif format_str == "Float32":
            self._type = np.float32
            self._size = 4
            self._normalization_constant = 1.0

    def converttofloat(self, data):
        return np.asarray(data, dtype=np.float32) / self._normalization_constant

    def convertfromfloat(self, data):
        return np.asarray(data * self._normalization_constant,
                          dtype=self._type)

    @property
    def size(self):
        return self._size

    @property
    def type(self):
        return self._type

    @property
    def pyaudioformat(self):
        if self._type == np.int8:
            return pyaudio.paInt8
        elif self._type == np.uint8:
            return pyaudio.paUInt8
        elif self._type == np.int16:
            return pyaudio.paInt16
        #elif self._type == np.int24:
        #    return pyaudio.paInt24
        elif self._type == np.int32:
            return pyaudio.paInt32
        elif self._type == np.float32:
            return pyaudio.paFloat32


def main():
    parser = argparse.ArgumentParser(description="Stream audio data from pipe")
    parser.add_argument("--inputs", "-i", type=int)
    parser.add_argument("--outputs", "-o", action="append", type=int)
    parser.add_argument("--framelength", "-fl", type=float, default=25.,
                        help="Frame length in milliseconds (default: {})"
                             .format(25.))
    parser.add_argument("--frameshift", "-fs", type=float, default=10.,
                        help="Frame shift in milliseconds (default: {})"
                             .format(10.))
    parser.add_argument("--samplingfrequency", "-sf", type=int, default=16000,
                        help="Sampling frequency (rate) (default: {})"
                             .format(16000))
    parser.add_argument("--numberofchannels", "-noc", type=int, default=8,
                        help="Number of channels (default: {})".format(8))
    parser.add_argument("--validchannels", "-vc", type=str,
                        default="0,1,2,3,4,5",
                        help="Comma-separated list of valid channel indices "
                             "(default: \"{}\")".format("0,1,2,3,4,5"))
    parser.add_argument("--notinterleaved", action="store_true",
                        help="Input is *not* interleaved")
    parser.add_argument("--inputfilepath", "-ifp", type=str,
                        help="Path to file which the valid input is written "
                             "to")
    parser.add_argument("--soundcard", "-sc", type=str,
                        help="(Prefix of) Soundcard name (default: \"{}\""
                             .format("audioinjector"), default="audioinjector")
    # TODO
    #parser.add_argument("--format", "-f", choices=["UInt8", "Int8", "Int16",
    #                                               "Int24", "Int32", "Float32"],
    #                    default="Int32")
    parser.add_argument("--format", "-f", choices=["UInt8", "Int8", "Int16",
                                                   "Int32", "Float32"],
                        default="Int32", help="Format of the input data "
                                              "(default: {})".format("Int32"))
    args = parser.parse_args()

    input_pipes = []
    if args.inputs is not None:
    	input_pipes = [os.fdopen(fd, 'rb') for fd in args.inputs]
    output_pipes = []
    if args.outputs is not None:
    	output_pipes = [os.fdopen(fd, 'wb') for fd in args.outputs]
    outputs = [pickle.Pickler(pipe, pickle.HIGHEST_PROTOCOL)
               for pipe in output_pipes]

    f = Format(args.format)
    valid_channels = np.array([int(chan)
                               for chan in args.validchannels.split(",")])

    frame_length = int((args.framelength * args.samplingfrequency) / 1000.0)
    frameshift = int((args.frameshift * args.samplingfrequency) / 1000.0)
    signal_buffer = SignalBuffer(frame_length, len(valid_channels))

    if len(input_pipes) == 0:
        pa = pyaudio.PyAudio()
        audioinjector_idx = None
        for idx in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(idx)
            if info["name"].lower().startswith(args.soundcard.lower()):
                audioinjector_idx = info["index"]
        if audioinjector_idx is None:
            raise ValueError("Given soundcard name \"{}\" not found"
                             .format(args.soundcard))
        stream = pa.open(format=f.pyaudioformat,
                         channels=args.numberofchannels,
                         rate=args.samplingfrequency,
                         input=True,
                         frames_per_buffer=frameshift)

    if args.inputfilepath is not None:
        wavfile = wave.open(args.inputfilepath, "wb")
        wavfile.setnchannels(len(valid_channels))
        wavfile.setsampwidth(f.size)
        wavfile.setframerate(args.samplingfrequency)

    while True:
        if len(input_pipes) == 0:
            in_data = np.fromstring(stream.read(frameshift,
                                                exception_on_overflow=False),
                                    dtype=f.type)
        else:
            # XXX: !!! no endianness defined !!!
            in_data = np.fromfile(inp, dtype=f.type,
                                  count=args.numberofchannels * frameshift)
        if args.notinterleaved:
            innovation = in_data.reshape((args.numberofchannels,
                                          frameshift)).T
        else:
            innovation = in_data.reshape((frameshift,
                                          args.numberofchannels))
        innovation = f.converttofloat(innovation[:, valid_channels])
        innovation = innovation.flatten('F')
        frame = signal_buffer.process(innovation)
        if args.inputfilepath is not None:
            wavfile.writeframes(f.convertfromfloat(innovation).tobytes())
        for out in output_pipes:
            out.write(frame.tobytes())
            out.flush()
        #for out_idx in range(len(outputs)):
        #    outputs[out_idx].dump(frame)
        #    outputs[out_idx].clear_memo()
        #    output_pipes[out_idx].flush()

    if args.inputfilepath is not None:
        wavfile.close()

    if len(input_pipes) == 0:
    	stream.stop_stream()
    	stream.close()
    	pa.terminate()

    for pipe in input_pipes:
        pipe.close()
    for pipe in output_pipes:
        pipe.close()


if __name__ == "__main__":

    # This is a hack to ensure the exceptions are logged if the module is
    # executed by the middleware.
    try:
        main()
    except Exception as e:
        import sys, traceback
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        with open("sig_buf.log", "w") as f:
            traceback.print_exc(file=f)
        raise
