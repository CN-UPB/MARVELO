#!/usr/bin/env python
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--FFTSize", type=int, default=8192)
    parser.add_argument("--logfiles", "-l",
                        default=["/home/asn/asn_server/Practise/dummy.log"],
                            action="append")

    return parser.parse_args()

#args = parse_arguments()
#inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]

#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

print 'Hello world!'

