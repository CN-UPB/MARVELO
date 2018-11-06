from pythonlib import Pipeinterface
import os,sys
import argparse
import getpass
import wave

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    return parser.parse_args()


args = parse_arguments()
pipe = Pipeinterface(args.inputs[0], 3072)
# Open a file for writing the received data
f = wave.open('audio.wav', 'wb')
# Parametrize the wave file: 16kHz, 32Bit Integer Data
f.setparams((6, 4, 16000, 0, 'NONE', 'not compressed'))

print('Okay on my way')
i = 0
k = 0
# Lifecycle: Stage 2 - Connect to far end node, it will immediately send data
while i < 2000:
    # Lifecyle: Stage 3 - Retrieve data from the stack
    DataDict = pipe.get_data(1)
    if DataDict["Size"] > 0:
       # Write Data to File
       print('Write Data')
       f.writeframesraw(DataDict["Data"])
       i += 1
    else:        
       k += 1
       print('No Data')

# close the file
f.close()
