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
    parser.add_argument("--SamplingRateOffset",
                            type=int,
                            default=0)
    parser.add_argument("--WindowSize",
                            type=int,
                            default=20)

    return parser.parse_args()

args = parse_arguments()

#init processing block
resampling_params = {"SamplingRateOffset": args.SamplingRateOffset, "WindowSize": args.WindowSize}
Resampling_Block = Resampling(resampling_params)

#open input pipes
inputs = ["null", "null"]
inputs[0] = os.fdopen(int(args.inputs[0]), 'rb')
inputs[1] = os.fdopen(int(args.inputs[1]), 'r') #not binary mode because dictionary is sent as string
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#open log files
logfiles = [open(f, 'w') for f in args.logfiles]

print("ready for processing - entering loop")
sys.stdout.flush()
counter = 0
while 1:
    if counter != 0: #no loopback data available for first iteration -> skip async part
        #do async processing (loopback!)
        sro_info_string = inputs[1].readline() #read 2nd input
        sro_info = ast.literal_eval(sro_info_string) #convert string to dictionary
        if sro_info['flag'] == True:
            Resampling_Block.process_async_data(sro_info['value']) #processing
        #write log data to file
        for file in logfiles:
            file.write(str(sro_info['value']) + '\n')
            file.flush()
        #print value for demonstration purposes
        print("sro value: " + str(sro_info['value']))
        sys.stdout.flush()

    #read data from pipe (40K items - 80KB)
    Data = np.fromfile(inputs[0], dtype='i2', count=40960)
    #do processing
    DataResult = Resampling_Block.process_data(Data)
    #write output data to pipe(s)
    for pipe in outputs:
        pipe.write(DataResult)
        pipe.flush()

    counter += 1

#close pipes and files
for pipe in inputs:
    pipe.close()
for pipe in outputs:
    pipe.close()
for file in logfiles:
    file.close()
