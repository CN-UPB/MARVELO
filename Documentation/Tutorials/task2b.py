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
x = inputs[0].readline()
z = int(x,10)
#x= inputs[0].readline()  
y = 2*z

print 'task2b output:'+'data received :'+ str(y)
sys.stdout.flush()
