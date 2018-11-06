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
    parser.add_argument("--Name",
                            default="/home/asn/asn_daemon/logfiles/rxdata")

    return parser.parse_args()


args = parse_arguments()


maxPacketNr = 7000
packetSize= 1024
data = []
#open pipes
fo = open(args.Name, "wb")
#fo2 = open("/home/asn/asn_daemon/logfiles/rxdataDummy", "wb")
input = os.fdopen(int(args.input), 'wb')

print " opened pipes to read: ", args.input

for i in range(maxPacketNr):
    print i
    frame = np.fromfile(input, dtype=np.int, count=packetSize)
    data.append(frame)
    fo.write( frame);
    fo.flush()

    #print " data :",frame
print("data read complete - exiting")
#for i in data:
#   fo2.write(i)
#   fo2.flush()
print("data read complete - exiting second writing")
fo2.close()

fo.close()
input.close()
