#!/usr/bin/env python
import os,sys
import argparse
from scipy import linalg as LA
import numpy as np
from scipy.io import wavfile

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                        default=["/home/asn/asn_daemon/logfiles/dummy.log"],
                            action="append")

    return parser.parse_args()

args = parse_arguments()
PACKETSIZE = 4096 #send data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)


inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
audio1= np.array([])
audio2= np.array([])
for pcount in range(13):
    signal1 = np.fromfile(inputs[0], dtype=np.uint8, count=4096)
    signal2 = np.fromfile(inputs[1], dtype=np.uint8, count=4096)
    audio1= np.append(audio1,signal1)
    audio2= np.append(audio2,signal2)

audio1 = audio1[:50000] / 255.0 - 0.5  # uint8 takes values from 0 to 255
audio2 = audio2[:50000] / 255.0 - 0.5  # uint8 takes values from 0 to 255

samplingRate = 8000
wavfile.write('/home/pi/asn_daemon/logfiles/rxcov1.wav', samplingRate, audio1[:50000])
wavfile.write('/home/pi/asn_daemon/logfiles/rxcov2.wav', samplingRate, audio2[:50000])


x = [audio1, audio2]
cov = np.cov(x)
d, E = LA.eigh(cov)
D = np.diag(d)


pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
pipes[0].write(D)
pipes[0].flush()

#print E.flags
E = E.copy(order='C')
#print 'new', E.flags

pipes[1].write(E)
pipes[1].flush()

pipes[2].write(np.array(x).reshape(1,100000))
pipes[2].flush()

for pipe in pipes:
    pipe.close()
print 'finished cov1***********************'
