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


y = str(random.randint(1,10))+'\n'

print 'sending data to pipe '
print y
sys.stdout.flush()
outputs = [os.fdopen(int(args.outputs[0]), 'wb')]
outputs[0].write(y)


sys.stdout.flush()
