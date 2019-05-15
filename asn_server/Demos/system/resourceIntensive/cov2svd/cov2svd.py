#!/usr/bin/env python
import os,sys
import argparse
from scipy import linalg as LA
import numpy as np
from scipy.io import wavfile
#%---------------- Start Additional Resource intesive method
import threading, time, sys

runTime = 5
fileName = "cov2SVD: "
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
#print 'inputs = ',args.inputs
#print 'outputs = ',args.outputs

inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
#print 'nr inputes = ', len(inputs)

norm = np.fromfile(inputs[0], dtype=np.float, count=100000)
norm=norm.reshape(2,50000)

xn = np.fromfile(inputs[1], dtype=np.float, count=100000)
xn=xn.reshape(2,50000)

cov2 = np.cov(np.multiply(norm, xn))
d_n, Y = LA.eigh(cov2)



source = np.dot(np.transpose(Y), xn)


samplingRate = 8000
wavfile.write('/home/asn/asn_daemon/logfiles/estimated1.wav', samplingRate, source[0])
wavfile.write('/home/asn/asn_daemon/logfiles/estimated2.wav', samplingRate, source[1])


for i in inputs:
    i.close()

#print 'finished cov2svd**********************************'

