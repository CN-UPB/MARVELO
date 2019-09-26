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



x = np.fromfile(inputs[0],dtype=np.float16,count=5)

print x

w = np.mean(x)
print w

#print 'task2b output:'+'data received :'+ str(z)
sys.stdout.flush()
