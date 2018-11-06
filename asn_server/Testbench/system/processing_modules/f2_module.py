#!/usr/bin/env python
import os,sys
import argparse
import numpy as np

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
fh = open("reult.txt","w")
fh.write(inputs[0])
fh.close()
