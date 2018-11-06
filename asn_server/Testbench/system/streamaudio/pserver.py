#!/usr/bin/env python
# send audio da
import pyaudio
import socket
import select
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--input", "-i",
                            default="")
    return parser.parse_args()
args = parse_arguments()

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
	
print pipe[0].readLine()
for pipe in pipes:
        pipe.close()
