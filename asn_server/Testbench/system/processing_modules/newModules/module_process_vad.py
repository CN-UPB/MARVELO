import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import Vad

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append",)
    parser.add_argument("--logfiles", "-l",
                            action="append")
    parser.add_argument("--EnergySmoothFactor",
                            type=float,
                            default=0.9)
    parser.add_argument("--OvershootFactor",
                            type=float,
                            default=2.0)

    return parser.parse_args()

args = parse_arguments()

#init processing block
vad_params = {"EnergySmoothFactor": args.EnergySmoothFactor, "OvershootFactor": args.OvershootFactor}
Vad_Block = Vad(vad_params)

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open log files
logfiles = [open(f, 'w') for f in args.logfiles]

print("ready for processing - entering loop")
sys.stdout.flush()
while 1:
    #read data from pipe (40K items - 80KB)
    Data = np.fromfile(input, dtype='i2', count=40960)
    #do processing
    vad_value = Vad_Block.process_data(Data)
    #write log data to file
    for file in logfiles:
        file.write(str(vad_value) + '\n')
        file.flush()

#close pipes and files
input.close()
for file in logfiles:
    file.close()
