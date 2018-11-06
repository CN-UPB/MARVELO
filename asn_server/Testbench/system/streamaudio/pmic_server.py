#!/usr/bin/env python
# send audio da
import pyaudio
import socket
import select
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--input", "-i",
                            default="")
    return parser.parse_args()
args = parse_arguments()

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
	
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096

audio = pyaudio.PyAudio()

def callback(in_data, frame_count, time_info, status):
    for pipe in pipes:
        pipe.write(in_data)
        pipe.flush()
    return (None, pyaudio.paContinue)


# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, stream_callback=callback)
stream.start_stream()

print "recording..."

try:
    while stream.is_active():
        time.sleep(0.1)
except KeyboardInterrupt:
    pass


print "finished recording"

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
for pipe in pipes:
        pipe.close()
