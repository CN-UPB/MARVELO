import argparse
import os
import sys
import time

import numpy as np
from fission.core.jobs import PythonJob

class MiddleJob(PythonJob):
    def run(self, a, b):
        value = int(a) + int(b)
        print(f"MiddleJob: {value}")
        return tuple([value]*2)

class task3a_Job(PythonJob):

    def run(self):

        # args = parse_arguments()
        # fds = [os.open(args.outputs[0], os.O_RDWR | os.O_CREAT)]

        for _ in range(10):
            y = np.array([2.0, 3, 4, 5, 6], dtype=np.float16)
            # print(y)
            yield y
            time.sleep(1)
            # print('sending data to pipe\n')
            sys.stdout.flush()
            # outputs = [os.fdopen(int(args.outputs[0]), 'wb')]
            # outputs[0].write(y)
            # for fd in fds:
            #     os.write(fd, y.tobytes())

        # outputs[0].write(y)
        # sys.stdout.flush()

        # for fd in fds:
        #     os.close(fd)
