#/usr/bin/env python
import pyaudio
import argparse
import socket
import sys
import os

# will send the voice
def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--input", "-i",
                            default="")
    return parser.parse_args()
print 'enter'
args = parse_arguments()	
input = os.fdopen(int(args.input), 'rb')

	
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096

# IPaddr = '192.168.43.180'
# IPaddr = '127.0.0.1'
# portNr = 4444
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((IPaddr,portNr))
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

try:
    while True:
	    data = np.fromfile(input, dtype='i2', count=CHUNK) #item size is 2 bytes!
        #data = s.recv(CHUNK)
            stream.write(data)
except KeyboardInterrupt:
    pass

print('Shutting down')
s.close()
stream.close()
input.close()
audio.terminate()
