#!/usr/bin/env python
import os,sys
import argparse
from scipy import linalg as LA
import numpy as np
from scipy.io import wavfile
#%---------------- Start Additional Resource intesive method
import threading, time, sys

runTime = 5
fileName = "NoiseWhitening: "
def r_intensive_func (fileName,itime):
    start = time.time()
    while time.time()-start <itime:
        v = int ((time.time()-start)/itime*100)
        sys.stdout.write("\r%s%%" % fileName+ str(v) )
        sys.stdout.flush()
        100**100
    sys.stdout.write("\r%s%%" % fileName+ str(100) )
    sys.stdout.flush()
    print "\nDone"+fileName + '**********************************'

thread = threading.Thread(target=r_intensive_func, args=[fileName,runTime])
print "Start\n"
thread.start()
#%---------------- End Additional Resource intesive method
def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                        default=["/home/asn/asn_daemon/logfiles/dummy.log"],
                            action="append")

    return parser.parse_args()

args = parse_arguments()
PACKETSIZE = 4096 #send data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)



inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]


Di_r = np.fromfile(inputs[0], dtype=np.float, count=4)
Di = Di_r.reshape((2, 2))

E = np.fromfile(inputs[1], dtype=np.float, count=4)
E=E.reshape(2,2)

x_r= np.fromfile(inputs[2], dtype=np.float, count=100000)
x = x_r.reshape((2,50000))

samplingRate = 8000
wavfile.write('/home/asn/asn_daemon/logfiles/rxwhiten1.wav', samplingRate, x[0])
wavfile.write('/home/asn/asn_daemon/logfiles/rxwhiten2.wav', samplingRate, x[1])


xn = np.dot(Di, np.dot(np.transpose(E), x))



#print 'outputs whiten = too long', len(xn)
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
for pipe in pipes:
    pipe.write(xn.reshape(1,100000))
    pipe.flush()



for pipe in pipes:
    pipe.close()
for i in inputs:
    i.close()

    
