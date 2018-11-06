#!/usr/bin/python
import os,sys
import argparse
import scipy.io.wavfile
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
PACKETSIZE = 4096 #send data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)



#open pipes
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
data = np.arange(7)
for pipe in pipes:
        pipe.write(data)

print("data transfer complete - exiting")

for pipe in pipes:
    pipe.close()

'''f


'''
