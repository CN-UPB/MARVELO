#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--mode", "-m", default=1, type=int)
    parser.add_argument("--inputs", "-i",  action="append")
    # parser.add_argument("--outputs", "-o", action="append")
    # parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
print('... parameter of printResults_mod.py: --mode for printing the microfone data: %d ...' % (int(args.mode)))
sys.stdout.flush()

# if you choose m=1 to run demo without time limitation
if int(args.mode) == 1:
    SROppm_act = np.float32(0)
    # main loop
    while True:
        inputData_0 = os.read(int(args.inputs[0]), 4)
        inputData_1 = os.read(int(args.inputs[1]), 4)
        inputData_0 = np.fromstring(inputData_0, dtype=np.float32)
        inputData_1 = np.fromstring(inputData_1, dtype=np.float32)
        if SROppm_act != inputData_0:
            SROppm_act = inputData_0
            #print('SRO_ppm = ', inputData_0, ', TimeOffset_smp = ', inputData_1)
            print('... estimates of the past signal segment: SRO_ppm = %6.3f; TimeOffset_smp = %6.3f' % (inputData_0, inputData_1))
            sys.stdout.flush()

# if you choose m=2 to run demo for specific time, you can here the recording
if int(args.mode) == 2:
    cnt_seg = 1                     # counter of signal segments
    sizeLoop = 15000                # for the length of the input signal of 15000 -> 120 s, 8000 -> 64 s
    ResetPeriod_NumFrInp = 3744     # for parameters of DXCP-PhaT-CL estimator: ResetPeriod_sec=30 and FFTshift_dxcp = 2**12
    text_file = open("Output.txt", "w")
    for pktCntr in range(sizeLoop):
        inputData_0 = os.read(int(args.inputs[0]), 4)
        inputData_1 = os.read(int(args.inputs[1]), 4)
        inputData_0 = np.fromstring(inputData_0, dtype=np.float32)
        inputData_1 = np.fromstring(inputData_1, dtype=np.float32)
        if pktCntr == cnt_seg*ResetPeriod_NumFrInp-1:
            #print(pktCntr, ': SRO_ppm = ', inputData_0, ', TimeOffset_smp = ', inputData_1)
            print('Past-Seg: SRO_ppm = %6.3f; TimeOffset_smp = %6.3f' % (inputData_0, inputData_1))
            sys.stdout.flush()
            text_file.write('Past-Seg: SRO_ppm = %6.3f; TimeOffset_smp = %6.3f\n' % (inputData_0, inputData_1))
            cnt_seg += 1

print('... finished :-).\n')
sys.stdout.flush()
text_file.close()
