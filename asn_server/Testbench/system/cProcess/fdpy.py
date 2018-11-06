#!/usr/bin/python
import os,sys
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--logfiles", "-l",
                            action="append")

    return parser.parse_args()


args = parse_arguments()


maxPacketNr = 4
packetSize= 1024
data = []
#open pipes
fo = open("/home/asn/asn_daemon/logfiles/rxdata", "wb")
input = os.fdopen(int(args.input), 'wb')

print " opened pipes to read: ", args.input

for i in range(maxPacketNr):
    print i
    frame = np.fromfile(input, dtype=np.int32, count=packetSize)
    fo.write( frame);
    fo.flush()
    data.append(frame)
    #print " data :",frame
print("data read complete - exiting")

fo.close()
input.close()
