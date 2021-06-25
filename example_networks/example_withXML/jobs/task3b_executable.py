#!/usr/bin/env python
import argparse
import struct

import numpy as np
import sys,os


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
# inputs = [os.fdopen(int(args.inputs[0]), 'rb')]
inputs = [open(f, 'rb') for f in args.inputs]

for _ in range(10):
    # x = np.fromfile(inputs[0],dtype=np.float16,count=5)
    in_bytes = inputs[0].read(2*5) # a buffer of 2 bytes * array length


    x = np.frombuffer(in_bytes,dtype=np.float16)
    # x = struct.unpack("!I", in_bytes)[0]
    print("received", x)
    sys.stdout.flush()
    w = np.mean(x)
    # sys.stdout.flush()
    print ("mean = ", w)
    sys.stdout.flush()

print ('task2b output:'+'data received :'+ str(w))
sys.stdout.flush()
sys.exit(0)