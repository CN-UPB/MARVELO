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
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

for pcount in range(13):
    print 'finished whiten',pcount
    sys.stdout.flush()
    Di_r = np.fromfile(inputs[0], dtype=np.float, count=4)
    Di = Di_r.reshape((2, 2))

    E = np.fromfile(inputs[1], dtype=np.float, count=4)
    E=E.reshape(2,2)

    x_r= np.fromfile(inputs[2], dtype=np.float, count=2*PACKETSIZE)
    x = x_r.reshape((2,PACKETSIZE))

    samplingRate = 8000
    # wavfile.write('/home/pi/asn_daemon/logfiles/rxwhiten1.wav', samplingRate, x[0])
    # wavfile.write('/home/pi/asn_daemon/logfiles/rxwhiten2.wav', samplingRate, x[1])


    xn = np.dot(Di, np.dot(np.transpose(E), x))



    #print 'outputs whiten = too long', len(xn)
    for pipe in pipes:
        pipe.write(xn.reshape(1,2*PACKETSIZE))
        pipe.flush()



print 'finished whiten**********************************'
# for i in inputs:
#         i.close()
#
# for pipe in pipes:
#         pipe.close()
#
