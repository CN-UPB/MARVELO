#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy.io import wavfile
import termTest

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--file", "-f",
                            default="")

    parser.add_argument("--param1","-p1",
                            type=int,
                            default=8192)
    parser.add_argument("--logfiles", "-l",
                            action="append")


    return parser.parse_args()
args = parse_arguments()
killer = termTest.GracefulKiller()
PACKETSIZE= 4096
sampleRate, data = scipy.io.wavfile.read(args.file)
#wavfile.write('/root/Desktop/tx.wav', sampleRate, data)

outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
sys.stdout.flush()
dataPos = 0
packetNrs = np.ceil(data.itemsize/PACKETSIZE)
while dataPos < 13:#packetNrs: #sample size is 2 bytes!
    for pipe in outputs:
        if killer.kill_now:
            dataPos = 100000000
            print 'exiting the loop gentely'
            sys.stdout.flush()

            break
        dataToSend = data[dataPos*PACKETSIZE:(dataPos+13)*PACKETSIZE+1]
        print args.file, dataPos

        if len(dataToSend)<4096:
           msgToSend = np.zeros(4096)
           msgToSend[0:len(dataToSend)]= dataToSend[:]
        else:
            msgToSend = dataToSend
        pipe.write(msgToSend) 
        #pipe.write(data[dataPos*PACKETSIZE:(dataPos+1)*PACKETSIZE])

        pipe.flush()

    dataPos += 1

logfiles = [open(f, 'w') for f in args.logfiles]

for file in logfiles:
            file.write(data[:])
            file.flush()
            print data

for file in logfiles:
    file.close()
	
for pipe in outputs:
    pipe.close()
print 'data len =', len(data), args.file
print 'shape = ' , data.shape
print 'finished readAudio*************'
sys.stdout.flush()
