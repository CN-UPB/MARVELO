#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy.io import wavfile
import signal
#%---------------- Start Additional Resource intesive method
import threading, time, sys

runTime = 5
fileName = "read$_2$: "
def r_intensive_func (fileName,itime):
    start = time.time()
    while time.time()-start <itime:
        v = int ((time.time()-start)/itime*100)
        sys.stdout.write("\r%s%%" % fileName+ str(v) )
        sys.stdout.flush()
        100**100
    print "\nDone"
thread = threading.Thread(target=r_intensive_func, args=[fileName,runTime])
print "Start\n"
thread.start()
#%---------------- End Additional Resource intesive method
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
                            default="mix2.wav")

    parser.add_argument("--param1","-p1",
                            type=int,
                            default=8192)
    parser.add_argument("--logfiles", "-l",
                        default=["/home/asn/asn_daemon/logfiles/dummy.log"])


    return parser.parse_args()
args = parse_arguments()
PACKETSIZE= 4096
sampleRate, data = scipy.io.wavfile.read(args.file)
#wavfile.write('/home/pi/tx.wav', sampleRate, data)
#data = "Hi from: ", args.file
#data = "Hi from: "
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
sys.stdout.flush()
dataPos = 0
packetNrs = np.ceil(data.itemsize/PACKETSIZE)
while dataPos < 13 and run:#packetNrs: #sample size is 2 bytes!
# while dataPos < 13:  # packetNrs: #sample size is 2 bytes!

    for pipe in outputs:
        # dataToSend = data[dataPos*PACKETSIZE:(dataPos+13)*PACKETSIZE+1]
        dataToSend = data[dataPos*PACKETSIZE:(dataPos+1)*PACKETSIZE]
        # print args.file, dataPos
        if len(dataToSend)<4096:
           msgToSend = np.zeros(4096)
           msgToSend[0:len(dataToSend)]= dataToSend[:]
        else:
            msgToSend = dataToSend

        try:
            pipe.write(msgToSend)
            #pipe.write(data[dataPos*PACKETSIZE:(dataPos+1)*PACKETSIZE])
            #print 'send data len =  ', len(msgToSend)
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
            print data

for file in logfiles:
    file.close()
	
for pipe in outputs:
    pipe.close()
print 'data len =', len(data), args.file
print 'shape = ' , data.shape

