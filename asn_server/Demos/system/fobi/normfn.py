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

xn = np.fromfile(inputs[0], dtype=np.float, count=100000)
xn = xn.reshape((2, 50000))

norm_xn = LA.norm(xn, axis=0)
norm = [norm_xn, norm_xn]

#print 'outputs whiten = too long', len(xn)
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
for pipe in pipes:
    pipe.write(np.array(norm).reshape(1,100000))
    pipe.flush()

#pipes[0].write(D)
#pipes[0].flush()

#pipes[1].write(E)
#pipes[1].flush()

for pipe in pipes:
    pipe.close()
print 'finished normfn**********************************'
for i in inputs:
    i.close()

    
