#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import Delay

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--FrameSize",
                            type=int,
                            default=1024)
    parser.add_argument("--Delay",
                            type=int,
                            default=1024)

    return parser.parse_args()

args = parse_arguments()

#init processing block
delay_params = {"FrameSize": args.FrameSize, "Delay": args.Delay}
Delay_Block = Delay(delay_params)

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
print("ready for processing - entering loop")
sys.stdout.flush()
while 1:
    #read data from pipe (40K items - 80KB)
    Data = np.fromfile(input, dtype='i2', count=args.FrameSize)
    #do processing
    delay_Data = Delay_Block.process_data(Data)
    #write result to output(s)
    for pipe in outputs:
        pipe.write(delay_Data)
        pipe.flush()

#close pipes
input.close()
for pipe in outputs:
    pipe.close()
