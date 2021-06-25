#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-12-13

import argparse, os, sys
import cPickle as pickle
import numpy as np

from diffuseness_estimator import DiffusenessEstimator


def main():
    parser = argparse.ArgumentParser(description="Estimate diffuseness")
    parser.add_argument("--inputs", "-i", action="append", type=int,
                        required=True)
    parser.add_argument("--outputs", "-o", action="append", type=int)
    parser.add_argument("--frameshift", "-fs", type=float, default=10.0,
                        help="Frame shift in milliseconds (default: 10.0)")
    parser.add_argument("--samplingfrequency", "-sf", type=int, default=16000,
                        help="Sampling frequency (rate) (default: {})"
                             .format(16000))
    parser.add_argument("--numberofchannelcombinations", "-nocc", type=int,
                        help="Number of channel combinations")
    parser.add_argument("--channelcombinations", "-cc", type=str,
                        help="Channel combinations. Format <channelIndex>-"
                             "<channelIndex>[,<channelIndex>-<channelIndex>]")
    parser.add_argument("--diffusenessbuffersize", type=float, default=2.,
                        help="Size of the buffer used to average the "
                             "diffuseness in seconds (default: {})".format(2.))
    args = parser.parse_args()

    input_pipes = [os.fdopen(fd, 'rb') for fd in args.inputs]
    inputs = [pickle.Unpickler(pipe) for pipe in input_pipes]
    output_pipes = []
    if args.outputs is not None:
        output_pipes = [os.fdopen(fd, 'wb') for fd in args.outputs]
    outputs = [pickle.Pickler(pipe, pickle.HIGHEST_PROTOCOL)
               for pipe in output_pipes]

    num_channel_combinations = 1
    if args.numberofchannelcombinations is not None:
        num_channel_combinations = args.numberofchannelcombinations
    elif args.channelcombinations is not None:
        channel_combinations = [tuple(map(int, cc.split("-")))
                                for cc in args.channelcombinations.split(",")]
        num_channel_combinations = len(channel_combinations)

    frameshift = int(args.frameshift * args.samplingfrequency / 1000.0)
    diffusenessbuffersize = int(args.diffusenessbuffersize *
                                args.samplingfrequency / frameshift)
    diffe = DiffusenessEstimator(diffusenessbuffersize,
                                 num_channel_combinations)

    while True:
        for inp in inputs:
            cdr = inp.load()
            diff = diffe.process(cdr)
            # compose the message containing the diffuseness and the
            frame = np.array([np.mean(diff)], dtype=np.float32)
            #message = str(np.mean(diff)) + "," + str(id)
            print('diff:', frame)
#            sys.stdout.flush()
            for out in output_pipes:
                out.write(frame.tobytes())
                out.flush()

    for pipe in input_pipes:
        pipe.close()
    for pipe in output_pipes:
        pipe.close()


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
