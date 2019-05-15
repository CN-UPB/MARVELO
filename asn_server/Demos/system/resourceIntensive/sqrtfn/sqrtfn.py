#!/usr/bin/env python
import os,sys
import argparse
from scipy import linalg as LA
import numpy as np
#%---------------- Start Additional Resource intesive method
import threading, time, sys

runTime = 5
fileName = "SqrtMatrix: "
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




inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]

audio1= np.array([])
D_r = np.fromfile(inputs[0], dtype=np.float, count=4)
D = D_r.reshape((2, 2))
#print 'inputs sqrtm = ', D
Di = LA.sqrtm(LA.inv(D))




#print 'outputs sqrtm = ',Di
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
pipes[0].write(Di)
pipes[0].flush()

#pipes[1].write(E)
#pipes[1].flush()

for pipe in pipes:
    pipe.close()
for i in inputs:
    i.close()

#print 'finished sqrtm*************'

