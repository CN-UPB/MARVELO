#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np
from py_modules.dxcp_phat import DXCPPhaT
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--config_file", "-c", default="")
    parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
print('... DXCP parameters are set in: ' + args.config_file + ' ...')
sys.stdout.flush()

# call constructor of DXCP-PhaT
Inst_DXCPPhaT = DXCPPhaT()

# main loop
sizeLoop = 15000
FrameSize_input = 128
inputData = np.zeros((FrameSize_input, 2))
startTime = time.time()
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
for pktCntr in range(sizeLoop):

    # get input data from pipes
    inputData_0 = os.read(int(args.inputs[0]), FrameSize_input*8)
    inputData_1 = os.read(int(args.inputs[1]), FrameSize_input*8)
    inputData_0 = np.fromstring(inputData_0, dtype=np.float64)
    inputData_1 = np.fromstring(inputData_1, dtype=np.float64)
    inputData[:, 0] = inputData_0  # x_1_ell
    inputData[:, 1] = inputData_1  # x_2_ell

    # execute DXCP-PhaT for one data frame inputData = x_12_ell
    OutputDXCPPhaT = Inst_DXCPPhaT.process_data(inputData)

    # set output vectors of this wrapper-function
    SROppm_est_out = np.float32(OutputDXCPPhaT['SROppm_est_out'])
    TimeOffsetEndSeg_est_out = np.float32(OutputDXCPPhaT['TimeOffsetEndSeg_est_out'])

    # write output data into pipes
    outputData = np.array([SROppm_est_out, TimeOffsetEndSeg_est_out], dtype=np.float32)
    pipes[0].write(outputData[0])
    pipes[1].write(outputData[1])

# print real-time factor
RTF_DXCPPhaTcl = (time.time() - startTime ) / 120
print('RTF of DXCP-PhaT: %6.3f' % (RTF_DXCPPhaTcl))
sys.stdout.flush()
