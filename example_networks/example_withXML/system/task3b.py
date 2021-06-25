#!/usr/bin/env python
import argparse
import numpy as np
import sys,os


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
inputs = [os.fdopen(int(args.inputs[0]), 'rb')]

for _ in range(5):
    # read data
    in_bytes = inputs[0].read(2 * 5)  # a buffer of 2 bytes (float16) * array length
    x = np.frombuffer(in_bytes, dtype=np.float16)
    print("reading", x)
    # x = np.fromfile(inputs[0],dtype=np.float16,count=5)
    print (x)
    w = np.mean(x)
    print ("mean=" ,w)
    sys.stdout.flush()

sys.stdout.flush()
for i in inputs:
    i.close()
sys.exit(0)