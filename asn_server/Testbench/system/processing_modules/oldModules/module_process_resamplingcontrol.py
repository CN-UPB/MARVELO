import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import ResamplingControl

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--SmoothFactor",
                            type=float,
                            default=0.99)
    parser.add_argument("--UpdateAfterNumObservations",
                            type=int,
                            default=30)

    return parser.parse_args()

args = parse_arguments()

#init processing block
rescontrol_params = {"SmoothFactor": args.SmoothFactor, "UpdateAfterNumObservations": args.UpdateAfterNumObservations}
ResamplingControl_Block = ResamplingControl(rescontrol_params)

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open output pipes
outputs = [os.fdopen(int(f), 'w') for f in args.outputs] #no binary mode because string is sent

print("ready for processing - entering loop")
sys.stdout.flush()
while 1:
    #read data from pipe
    coherenceDrift = np.fromfile(input, dtype=np.float64, count=1) #receive float64 (as numpy array with 1 element)
    #do processing
    sro_info = ResamplingControl_Block.process_data(coherenceDrift[0])
    #write result to output
    for pipe in outputs:
        pipe.write(str(sro_info) + '\n') #sro_info is a dictionary (use default conversion to string)
        pipe.flush()

#close pipes
input.close()
for pipe in outputs:
    pipe.close()
