#!/usr/bin/env python
import argparse
import time

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
outputs = [os.fdopen(int(args.outputs[0]), 'wb')]

for _ in range(5):
    #generate data
    y = np.array([2.0,3,4,5,6],dtype=np.float16)
    print (y)
    print ('sending data to pipe\n')
    # outputs[0].write(y.tobytes())
    os.write( int(args.outputs[0]),y.tobytes())
    sys.stdout.flush()

    time.sleep(1)
print("all data sent")
for o in outputs:
    o.close()
sys.exit(0)