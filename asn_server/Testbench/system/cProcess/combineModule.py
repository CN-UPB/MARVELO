#!/usr/bin/python
import os,sys
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                            action="append")


    return parser.parse_args()


args = parse_arguments()


maxPacketNr = 7000
packetSize= 1024
data = []
#open pipes
#fo = open("/home/asn/asn_daemon/logfiles/rxdata1", "wb")
#fo2 = open("/home/asn/asn_daemon/logfiles/rxdata2", "wb")
#fo3 = open("/home/asn/asn_daemon/logfiles/rxdatacombine", "wb")
inputs = [os.fdopen(int(f), 'rb') for f in args.input]
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
print " opened pipes to read: ", args.input
sys.stdout.flush()
for i in range(maxPacketNr):
    print i , "combine"
    sys.stdout.flush()
    frame0 = np.fromfile(inputs[0], dtype=np.int, count=packetSize)
    frame1 = np.fromfile(inputs[1], dtype=np.int, count=packetSize)
    print i , "read"
    sys.stdout.flush()
    outputs[0].write(frame0)
    outputs[0].flush()
    outputs[0].write(frame1)
    #combined = np.append(frame0,frame1)
    #outputs[0].write(np.ones(1024)*1000)
    outputs[0].flush()
    #fo.write( frame0);
    #fo.flush()
    #fo2.write( frame1);
    #fo2.flush()
    data.append(frame0)
    data.append(frame1)

    #print " data :",frame
#print("data read complete - exiting")
#for i in data:
#   fo3.write(i)
#   fo3.flush()
print("data combined !")
#fo3.close()
#fo2.close()
#fo.close()
for i in inputs:
   i.close()
for o in outputs:
   o.close()
