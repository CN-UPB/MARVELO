#!/usr/bin/env python
import os,sys
import ast
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import Resampling

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                            action="append")
    parser.add_argument("--OutFrameSize",
                            type=int,
                            default=4096)
    parser.add_argument("--InFrameSize",
                            type=int,
                            default=1024)
    parser.add_argument("--FrameShift",
                            type=int,
                            default=1024)
    parser.add_argument("--Name", "-n",
                            default="Reframing CH1")

    return parser.parse_args()

args = parse_arguments()

#init processing block
resampling_params = reframe_params = {"InFrameSize": args.InFrameSize, "OutFrameSize": args.OutFrameSize, "FrameShift": args.FrameShift}
Reframe_Block = Resampling(reframe_params,args.Name)

#open input pipes
inputs = ["null", "null"]
inputs[0] = os.fdopen(int(args.inputs[0]), 'rb')
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#open log files
logfiles = [open(f, 'w') for f in args.logfiles]

print("ready for processing - entering loop")
sys.stdout.flush()
counter = 0
while 1:

    #read data from pipe (40K items - 80KB)
    Data = np.fromfile(inputs[0], dtype='i2', count=args.InFrameSize)
    #do processing
    DataResult = Reframe_Block.process_data(Data)
    #write output data to pipe(s)
    for pipe in outputs:
        pipe.write(DataResult['value'])
        pipe.flush()

    counter += 1

#close pipes and files
for pipe in inputs:
    pipe.close()
for pipe in outputs:
    pipe.close()
for file in logfiles:
    file.close()


