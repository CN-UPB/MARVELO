#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy.io import wavfile
import signal

#killer = termTest.GracefulKiller()
run = True
def handler_stop_signals(signum, frame):
    global run
    run = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")

    parser.add_argument("--file", "-f",
                            default="mix1.wav")

    parser.add_argument("--param1","-p1",
                            type=int,
                            default=8192)
    parser.add_argument("--logfiles", "-l",
                        default=["/home/asn/asn_daemon/logfiles/dummy.log"],action="append")


    return parser.parse_args()
args = parse_arguments()
PACKETSIZE= 8192*2
sampleRate, data = scipy.io.wavfile.read(args.file)
#wavfile.write('/home/pi/tx.wav', sampleRate, data)
#data = "Hi from: ", args.file
#data = "Hi from: "
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
sys.stdout.flush()
dataPos = 0
packetNrs = np.ceil(data.itemsize/PACKETSIZE)
while dataPos < 3 and run:#packetNrs: #sample size is 2 bytes!
# while dataPos < 13:  # packetNrs: #sample size is 2 bytes!

    for pipe in outputs:
        # dataToSend = data[dataPos*PACKETSIZE:(dataPos+13)*PACKETSIZE+1]
        dataToSend = data[dataPos*PACKETSIZE:(dataPos+1)*PACKETSIZE]
        # print args.file, dataPos
        if len(dataToSend)<PACKETSIZE:
           msgToSend = np.zeros(PACKETSIZE)
           msgToSend[0:len(dataToSend)]= dataToSend[:]
        else:
            msgToSend = dataToSend

        try:
            pipe.write(msgToSend)
            #pipe.write(data[dataPos*PACKETSIZE:(dataPos+1)*PACKETSIZE])
            print '****send data =  ', args.file, '**with packet',dataPos
            sys.stdout.flush()
            pipe.flush()
        except:
            print "writing has been interupted"
            sys.stdout.flush()

    dataPos += 1
'''for pipe in outputs:
        pipe.write(data[:])
        pipe.flush()'''

logfiles = [open(f, 'w') for f in args.logfiles]

for file in logfiles:
            file.write(data[:])
            file.flush()
            #print data

for file in logfiles:
    file.close()
	
# for pipe in outputs:
#     pipe.close()
print 'data len =', len(data), args.file
print 'shape = ' , data.shape

