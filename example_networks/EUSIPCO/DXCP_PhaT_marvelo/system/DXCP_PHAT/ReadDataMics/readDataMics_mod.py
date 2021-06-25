#!/usr/bin/env python
import os
import sys
import wave
import pyaudio
import argparse
import numpy as np


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--mode", "-m", default=1, type=int)        # mode for reading the microfone data
    parser.add_argument("--chanOut1", "-c1", default=1, type=int)   # microfon-ID used for output channel-1
    parser.add_argument("--chanOut2", "-c2", default=2, type=int)   # microfon-ID used for output channel-2
    # parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    # parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
print('... parameters of readDataMics_mod.py: --mode: %d, --chanOut1: %d, --chanOut2: %d ...'
      % (int(args.mode), int(args.chanOut1), int(args.chanOut2)))
sys.stdout.flush()
if int(args.chanOut1) == int(args.chanOut2):
    print('... ERROR in xml-file with readDataMics_mod.py: -ch1 and -ch2 should be set to different values !!! ...')
    sys.stdout.flush()
    sys.exit()

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 4
RESPEAKER_WIDTH = 2
# run getDeviceInfo.py to get index
RESPEAKER_INDEX = 2  # refer to input device id
#CHUNK = 1024
CHUNK = 128
if int(args.mode) == 2:
    RECORD_SECONDS = 65
    WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

stream = p.open(
            rate=RESPEAKER_RATE,
            format=p.get_format_from_width(RESPEAKER_WIDTH),
            channels=RESPEAKER_CHANNELS,
            input=True,
            input_device_index=RESPEAKER_INDEX,)
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

# if you choose m=1 to run demo without time limitation
if int(args.mode) == 1:
    while True:
        data = stream.read(CHUNK)  # mic-1: [0 4 8...], mic-2: [1 5 9...], mic-3: [2 6 10...], mic-4: [3 7 11...]
        chanOut1 = np.fromstring(data, dtype=np.int16)[int(args.chanOut1-1)::4].copy(order='C')
        chanOut2 = np.fromstring(data, dtype=np.int16)[int(args.chanOut2-1)::4].copy(order='C')
        pipes[0].write(chanOut1)
        pipes[1].write(chanOut2)
        pipes[0].flush()
        pipes[1].flush()

# if you choose m=2 to run demo for specific time, you can here the recording
if int(args.mode) == 2:
    print("* do recording")
    frames = []
    for i in range(0, int(RESPEAKER_RATE * RECORD_SECONDS / CHUNK)):
        data = stream.read(CHUNK)
        chanOut1 = np.fromstring(data, dtype=np.int16)[int(args.chanOut1 - 1)::4].copy(order='C')
        chanOut2 = np.fromstring(data, dtype=np.int16)[int(args.chanOut2 - 1)::4].copy(order='C')
        pipes[0].write(chanOut1)
        pipes[1].write(chanOut2)
        pipes[0].flush()
        pipes[1].flush()
        frames.append(data)

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(RESPEAKER_CHANNELS)
    wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
    wf.setframerate(RESPEAKER_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print("* recording done")

stream.stop_stream()
stream.close()
p.terminate()
