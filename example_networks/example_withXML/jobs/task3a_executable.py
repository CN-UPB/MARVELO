#!/usr/bin/env python
import argparse
import time

import numpy as np
import random
import sys
import os


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--outputs", "-o",
                        action="append")

    return parser.parse_args()


args = parse_arguments()
fds = [os.open(args.outputs[0], os.O_RDWR | os.O_CREAT)]

for _ in range(10):
    y = np.array([2.0, 3, 4, 5, 6], dtype=np.float16)
    print(y)
    print('sending data to pipe\n')
    sys.stdout.flush()
    # outputs = [os.fdopen(int(args.outputs[0]), 'wb')]
    # outputs[0].write(y)
    for fd in fds:
        os.write(fd,y.tobytes())
    time.sleep(0.1)


# outputs[0].write(y)
sys.stdout.flush()

for fd in fds:
    os.close(fd)
sys.exit(0)
