import os,sys
import argparse
import numpy as np
import scipy.io.wavfile

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")

    return parser.parse_args()

args = parse_arguments()

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

print("ready for processing - entering loop")
sys.stdout.flush()
while 1:
    #read data from pipe (40K items - 80KB)
    Data = np.fromfile(input, dtype='i2', count=40960)
    #write data to multiple outputs
    for pipe in outputs:
        pipe.write(Data)
        pipe.flush()

#close pipes
input.close()
for pipe in outputs:
    pipe.close()
