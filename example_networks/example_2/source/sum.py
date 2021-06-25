import sys
import os
import argparse
from time import sleep
import struct

parser = argparse.ArgumentParser(description='arguments')
parser.add_argument("--inputs", "-i", action="append")
parser.add_argument("--outputs", "-o", action="append")
args = parser.parse_args()

if args.inputs:
    inputs = [open(f, 'rb') for f in args.inputs]

value = 0

while(True):
    in_bytes = inputs[0].read(4)
    if not in_bytes:
        exit(0)
    recved = struct.unpack("!I", in_bytes)[0]

    value += recved
    print(recved)
    sys.stdout.flush()

    with open("executable.txt", "a") as f:
        f.write(f"{recved}\n")
