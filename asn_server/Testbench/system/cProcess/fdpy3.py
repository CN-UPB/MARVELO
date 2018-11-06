#!/usr/bin/python
import os,sys
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                            action="append")

    return parser.parse_args()


args = parse_arguments()


maxPacketNr = 6000
packetSize= 1024
data = []
#open pipes
fo = open("/home/asn/asn_daemon/logfiles/rxdata1", "wb")
fo2 = open("/home/asn/asn_daemon/logfiles/rxdata2", "wb")
fo3 = open("/home/asn/asn_daemon/logfiles/rxdatacombine", "wb")
inputs = [os.fdopen(int(f), 'rb') for f in args.input]

print " opened pipes to read: ", args.input

for i in range(maxPacketNr):
    print i
    frame0 = np.fromfile(inputs[0], dtype=np.int, count=packetSize)
    frame1 = np.fromfile(inputs[1], dtype=np.int, count=packetSize)
    fram0Reshap = np.reshape(frame0,(128,8))
    fram1Reshap = np.reshape(frame1,(128,8))
    frameR = np.append(fram0Reshap,fram1Reshap,axis=1)
    frameToWrite=  np.reshape(frameR,(1,-1))
    fo.write( frame0);
    fo.flush()
    fo2.write( frame1);
    fo2.flush()
    data.append(frameToWrite)
    #data.append(frame1)

    #print " data :",frame
print("data read complete - exiting")
count  = 0
for i in data:
#  if count<2:
   fo3.write(i)
   fo3.flush()
#  count=count+1
print("data read complete - exiting second writing")
fo3.close()
fo2.close()
fo.close()
for i in inputs:
   i.close()
