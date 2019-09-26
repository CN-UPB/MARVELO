#!/usr/bin/env python
import argparse
import numpy as np
import random
import sys
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--outputs", "-o",
                            action="append")
    
    

    return parser.parse_args()

args = parse_arguments()

y = np.array([2.0,3,4,5,6],dtype=np.float16)
print y

print 'sending data to pipe\n'

sys.stdout.flush()
outputs = [os.fdopen(int(args.outputs[0]), 'wb')]
outputs[0].write(y)

#outputs[0].write(y)
sys.stdout.flush()
