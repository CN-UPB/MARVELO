#!/usr/bin/env python

import pyaudio
import wave
import os
import sys
import argparse
import numpy as np
#from scipy import io            # to load .mat file
from scipy.io import wavfile    # to read .wav file


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    # parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    # parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 4
RESPEAKER_WIDTH = 2
# run getDeviceInfo.py to get index
RESPEAKER_INDEX = 2  # refer to input device id
#CHUNK = 1024
CHUNK = 128
RECORD_SECONDS = 70
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

stream = p.open(
            rate=RESPEAKER_RATE,
            format=p.get_format_from_width(RESPEAKER_WIDTH),
            channels=RESPEAKER_CHANNELS,
            input=True,
            input_device_index=RESPEAKER_INDEX,)

print("* recording")

frames = []

# if you choose to run for specific time, you can here the recording
for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
#while True:
    data = stream.read(CHUNK)
    #channel1 = np.fromstring(data, dtype=np.float32)[1::4].copy(order='C')
    #channel2 = np.fromstring(data, dtype=np.float32)[2::4].copy(order='C')
    channel1 = np.fromstring(data, dtype=np.int16)[1::4].copy(order='C')
    channel2 = np.fromstring(data, dtype=np.int16)[2::4].copy(order='C')
    pipes[0].write(channel1)
    pipes[1].write(channel2)
    pipes[0].flush()
    pipes[1].flush()
    frames.append(data)

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(RESPEAKER_CHANNELS)
wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
wf.setframerate(RESPEAKER_RATE)
wf.writeframes(b''.join(frames))
wf.close()

