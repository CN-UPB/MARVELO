#!/usr/bin/env python


import argparse, os, sys, socket
import cPickle as pickle
import numpy as np

from utils import * 

def main():
    parser = argparse.ArgumentParser(description="arguments")
    
    parser.add_argument("--inputs", "-i", action="append", type=int)
    parser.add_argument("--outputs", "-o", action="append", type=int)
    parser.add_argument("--id", action="append", type=str)

    args = parser.parse_args()
    inputs = [PipeReader(fd, 1) for fd in args.inputs]

    ips = [socket.inet_aton(ip) for ip in args.id]
    
    output_pipes = []
    if args.outputs is not None:
        output_pipes = [os.fdopen(fs, 'wb') for fs in args.outputs]
    
    diffs = np.zeros((len(inputs), 30))
    
    # needed to prevent oszillation
    previous = -1
    minOccureneces = 20
    occurences = minOccureneces

    counter = 0
    # needed to show the value only every nth (e.g. 10th) time
    printCounter = 0
    while True:
        
        # this counter is needed to ignore the 0 which fill the array at the beginning
        if counter < 30:
            counter += 1

        printCounter += 1
        # create a place for the new values 
        diffs = np.roll(diffs, 1, axis= 1)
        
        # read the new values
        for i in range(len(inputs)):
            sys.stdout.flush()
            frame = inputs[i].read_block()
            diffs[i][0] = frame
        
        #print("diffs:\n" + str(diffs))
        # calculate the mean for the different inputs
        means = np.mean(diffs[:, :counter], axis=1)
        #print("means: \n" + str(means))
        frame = means.flatten()
        argmax = np.argmin(frame)
        #print("argmax: " + str(argmax))
        #sys.stdout.flush()
        
        if argmax != previous:
            if occurences < minOccureneces:
                argmax = previous
                occurences += 1
            else:
                previous = argmax
                occurences = 0
        else:
            occurences += 1

        # send all means on the first pipe
        if len(output_pipes) > 0:
            output_pipes[0].write(frame.astype(np.float32).tobytes())
            output_pipes[0].flush()
        # send the ip of the device with the highest cdr on the second pipe
        if len(output_pipes) > 1:
            output_pipes[1].write(ips[argmax])
            output_pipes[1].flush()
        
        if printCounter > 10:
            printCounter = 0
            # print the ip of the divice with the highest cdr
            print("PI with IP " + socket.inet_ntop(socket.AF_INET, ips[argmax]) + " is closest to source")
            for i in range(len(means)):
                print(socket.inet_ntop(socket.AF_INET, ips[i]) + " has the value " + str(means[i]))
            sys.stdout.flush()
            
        



if __name__ == "__main__":

    # This is a hack to ensure the exceptions are logged if the module is
    # executed by the middleware.
    try:
        main()
    except Exception as e:
        import sys, traceback
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        with open("diff_est.log", "w") as f:
            traceback.print_exc(file=f)
        raise
