import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import CoherenceDriftEstimator

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--FFTSize",
                            type=int,
                            default=8192)
    parser.add_argument("--CoherenceTimeDelay",
                            type=int,
                            default=1024)
    parser.add_argument("--MaximumSRO",
                            type=int,
                            default=300) 
    parser.add_argument("--WelchShift",
                            type=int,
                            default=1024)

    return parser.parse_args()

args = parse_arguments()

#init processing block
cw_params = {"FFTSize": args.FFTSize, "CoherenceTimeDelay": args.CoherenceTimeDelay, "MaximumSRO": args.MaximumSRO, "WelchShift": args.WelchShift}
CoherenceDriftEstimator_Block = CoherenceDriftEstimator(cw_params)

#open input pipes
inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

print("ready for processing - entering loop")
sys.stdout.flush()
while 1:
    #read data from pipes
    coherence1 = np.fromfile(inputs[0], dtype=np.complex128, count=8192)
    coherence2 = np.fromfile(inputs[1], dtype=np.complex128, count=8192)

    #do processing
    coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1, coherence2)

    #write result to output(s)
    for pipe in outputs:
        pipe.write(coherenceDrift)
        pipe.flush()

#close pipes
for pipe in inputs:
    pipe.close()
for pipe in outputs:
    pipe.close()
