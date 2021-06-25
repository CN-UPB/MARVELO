#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-12-13

import argparse, os, sys
import cPickle as pickle
from utils import *

from power_spectra_estimator import PowerSpectraEstimator


def main():
    parser = argparse.ArgumentParser(description="Estimate power spectra")
    parser.add_argument("--inputs", "-i", action="append", type=int,
                        required=True)
    parser.add_argument("--outputs", "-o", action="append", type=int)
    parser.add_argument("--framelength", "-fl", type=float, default=25.,
                        help="Frame length in milliseconds (default: {})"
                             .format(25.))
    parser.add_argument("--samplingfrequency", "-sf", type=int, default=16000,
                        help="Sampling frequency (rate) (default: {})"
                             .format(16000))
    parser.add_argument("--numberofchannels", "-noc", type=int, default=2,
                        help="Number of channels (default: {})".format(2))
    parser.add_argument("--fftlength", type=int, default=512,
                        help="DFT length in samples (default: {})".format(512))
    parser.add_argument("--smoothingfactor", type=float, default=.95,
                        help="Smoothing factor (default: {})".format(.95))
    parser.add_argument("--minimumfrequency", type=float, default=125.,
                        help="Minimum evaluation frequency in Hz (default: {})"
                             .format(125.))
    parser.add_argument("--maximumfrequency", type=float, default=3500.,
                        help="Maximum evaluation frequency in Hz (default: {})"
                             .format(3500.))
    args = parser.parse_args()

    frame_length = int(args.framelength * args.samplingfrequency / 1000.0)
    min_bin = int((args.minimumfrequency * args.fftlength) /
                  args.samplingfrequency)
    max_bin = int((args.maximumfrequency * args.fftlength) /
                  args.samplingfrequency)
    pse = PowerSpectraEstimator(frame_length, args.fftlength,
                                args.smoothingfactor, min_bin, max_bin,
                                args.numberofchannels)

    #input_pipes = [os.fdopen(fd, 'rb') for fd in args.inputs]
    #inputs = [pickle.Unpickler(pipe) for pipe in input_pipes]
    inputs = [PipeReader(fd, (frame_length, args.numberofchannels)) for fd in args.inputs]

    output_pipes = []
    if args.outputs is not None:
    	output_pipes = [os.fdopen(fd, 'wb') for fd in args.outputs]
    outputs = [pickle.Pickler(pipe, pickle.HIGHEST_PROTOCOL)
               for pipe in output_pipes]

    
    

    while True:
        for inp in inputs:
            frame = inp.read_block()
            psds = pse.process(frame)
            #psds = psds.flatten('F')
            #for out in output_pipes:
            #    out.write(psds.tobytes())
            #    out.flush()
            for out_idx in range(len(outputs)):
                outputs[out_idx].dump(psds)
                outputs[out_idx].clear_memo()
                output_pipes[out_idx].flush()

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
        with open("psd_est.log", "w") as f:
            traceback.print_exc(file=f)
        raise
