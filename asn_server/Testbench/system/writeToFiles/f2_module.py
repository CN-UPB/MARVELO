#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")

 
    return parser.parse_args()

args = parse_arguments()
inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]


# Open a file
#fdi = os.fdopen(int(2))
#print fdi
#fdi.close
#print "Closed the file successfully!!"
fh = open("/home/asn/asn_daemon/logfiles/result.txt","w")
fh.write('start reading\n')
nrAttempt = 3
#for trial in range(nrAttempt):
fh.write(inputs[0].readline() )
#  fh.flush()
#  time.sleep(1)
fh.write('done reading\n')
#fh.flush()
fh.close()
for i in inputs:
 i.close()
