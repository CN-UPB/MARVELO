#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-12-13

import argparse, os
import cPickle as pickle
from itertools import combinations
from utils import *

from signal_coherence_estimator import SignalCoherenceEstimator


def main():
    parser = argparse.ArgumentParser(description="Estimate signal coherence")
    parser.add_argument("--inputs", "-i", action="append", type=int,
                        required=True)
    parser.add_argument("--outputs", "-o", action="append", type=int)
    parser.add_argument("--samplingfrequency", "-sf", type=int, default=16000,
                        help="Sampling frequency (rate) (default: {})"
                             .format(16000))
    parser.add_argument("--numberofchannels", "-noc", type=int, default=2,
                        help="Number of channels (default: {})".format(2))
    parser.add_argument("--fftlength", type=int, default=512,
                        help="DFT length in samples (default: {})".format(512))
    parser.add_argument("--minimumfrequency", type=float, default=125.,
                        help="Minimum evaluation frequency in Hz (default: {})"
                             .format(125.))
    parser.add_argument("--maximumfrequency", type=float, default=3500.,
                        help="Maximum evaluation frequency in Hz (default: {})"
                             .format(3500.))
    parser.add_argument("--channelcombinations", "-cc", type=str,
                        help="Channel combinations for coherence estimation. "
                             "Format <channelIndex>-<channelIndex>"
                             "[,<channelIndex>-<channelIndex>]")
    args = parser.parse_args()

    input_pipes = [os.fdopen(fd, 'rb') for fd in args.inputs]
    inputs = [pickle.Unpickler(pipe) for pipe in input_pipes]
    #inputs = [PipeReader(fd, (frame_length, args.numberofchannels)) for fd in args.inputs]
    output_pipes = []
    if args.outputs is not None:
        output_pipes = [os.fdopen(fd, 'wb') for fd in args.outputs]
    outputs = [pickle.Pickler(pipe, pickle.HIGHEST_PROTOCOL)
               for pipe in output_pipes]

    min_bin = int((args.minimumfrequency * args.fftlength) /
                  args.samplingfrequency)
    max_bin = int((args.maximumfrequency * args.fftlength) /
                  args.samplingfrequency)

    if args.channelcombinations is not None:
        channel_combinations = [tuple(map(int, cc.split("-")))
                                for cc in args.channelcombinations.split(",")]
    else:
        channel_combinations = [cc
                                for cc in
                                combinations(range(args.numberofchannels), 2)]

    sce = SignalCoherenceEstimator(args.numberofchannels, channel_combinations,
                                   min_bin, max_bin)

    while True:
        for inp in inputs:
            psds = inp.load()
            coh = sce.process(psds)
            for out_idx in range(len(outputs)):
                outputs[out_idx].dump(coh)
                outputs[out_idx].clear_memo()
                output_pipes[out_idx].flush()

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
        with open("coh_est.log", "w") as f:
            traceback.print_exc(file=f)
        raise
