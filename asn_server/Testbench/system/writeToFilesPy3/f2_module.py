#!/usr/bin/env python3
import os,sys
import argparse
import numpy as np
import io

import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")

 
    return parser.parse_args()

print ("*****reading file*****")

args = parse_arguments()
#inputss = [os.lseek(int(f),0,0) for f in args.inputs]
print ([int(i) for i in args.inputs])
chunckSize = 4096
totalRec = []
for nrPkt in range(0,int(1000)):
    inputs = [os.read(int(f),  chunckSize*8) for f in args.inputs]
    inputs = [np.fromstring(s,dtype=np.float) for s in inputs]
    print ("reading pkt", str(nrPkt))
    sys.stdout.flush()

    totalRec=np.concatenate((totalRec,inputs[0]),axis=0)
#inputs = [ io.TextIOWrapper(reader) for reader in inputss]
print ('********rec length', len(totalRec))
# print ('********rec length', len(inputs[0]))

# Open a file
#fdi = os.fdopen(int(2))
#print f
#fdi.close
#print "Closed the file successfully!!"
#fh = open("/home/asn/asn_daemon/logfiles/result.txt","wb")
#fh.write('start reading\n'.encode())
nrAttempt = 3
#for trial in range(nrAttempt):
rec_data  = totalRec#np.fromfile(inputs[0], dtype=np.int, count=4)
print(totalRec)
#fh.write(rec_data)
np.savetxt("/home/asn/asn_daemon/logfiles/result.txt",rec_data)
#  fh.flush()
#  time.sleep(1)
#fh.write('done reading\n'.encode())
#fh.flush()
#fh.close()
#for i in inputs:
# i.close()
