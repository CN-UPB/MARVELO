#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import CoherenceWelch

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--FFTSize",
                            type=int,
                            default=8192)
    parser.add_argument("--WelchShift",
                            type=int,
                            default=1024)
    parser.add_argument("--WindowType",
                            default="Hann")

    return parser.parse_args()

args = parse_arguments()

#init processing block
psd_params = {"FFTSize": args.FFTSize, "WelchShift": args.WelchShift, "WindowType": args.WindowType}
CW_Block = CoherenceWelch(psd_params)

#open input pipes
inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

print("ready for processing CW - entering loop")
sys.stdout.flush()

sys.stdout.flush()
while 1:
    #read data from pipe (40K items - 80KB)
    Data1 = np.fromfile(inputs[0], dtype='i2', count=40960)
    Data2 = np.fromfile(inputs[1], dtype='i2', count=40960)
    #do processing
    coherence = CW_Block.process_data(Data1, Data2)
    #print 'CW =', sum(Data1-Data2)
    #sys.stdout.flush()
    # outputs[0].write(Data1)
    # outputs[0].flush()
    # outputs[1].write(Data2)
    # outputs[1].flush()
    # outputs[2].write(coherence)
    # outputs[2].flush()

    #write result to output(s)
    for pipe in outputs:
        pipe.write(coherence)
        pipe.flush()

#close pipes
for pipe in inputs:
    pipe.close()
for pipe in outputs:
    pipe.close()
