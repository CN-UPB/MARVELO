#!/usr/bin/env python3
import os
import sys
#import wave
#import pyaudio
import argparse
import numpy as np
from py_modules.dxcp_phat import DXCPPhaT
from config.Parameters_DXCPPhaT import *
from utils import PipeReader
from scipy.io.wavfile import write

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--config_file", "-c", default="")
    parser.add_argument("--mode", "-m", default=2, type=int)
    parser.add_argument("--record", "-r", default=0, type=int)
    parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()

#FrameSize_input = 128
if (int(args.mode) == 1):
    inputDataType = 'int16'
    inputData = np.int16(np.zeros((FrameSize_input, 2)))
    reader1 = PipeReader(int(args.inputs[0]), (int(FrameSize_input), int(1)), np.int16)
    reader2 = PipeReader(int(args.inputs[1]), (int(FrameSize_input), int(1)), np.int16)
if (int(args.mode) == 2):
    inputDataType = 'float32'
    inputData = np.float32(np.zeros((FrameSize_input, 2)))
    reader1 = PipeReader(int(args.inputs[0]), (int(FrameSize_input), int(1)), np.float32)
    reader2 = PipeReader(int(args.inputs[1]), (int(FrameSize_input), int(1)), np.float32)

print('... parameters of DXCP-PhaT are set in: ' + args.config_file + '; with input data type: ' + inputDataType + ' ...')
sys.stdout.flush()

# call constructor of DXCP-PhaT
Inst_DXCPPhaT = DXCPPhaT()

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

# main loop
NumSegs_toSave = 3
flagSave = 1
while True:
    # get input data from pipes
    inputData[:, 0] = reader1.read_block()[:, 0]
    inputData[:, 1] = reader2.read_block()[:, 0]

    # execute DXCP-PhaT for one data frame inputData = x_12_ell
    OutputDXCPPhaT = Inst_DXCPPhaT.process_data(np.float32(inputData))

    # set output vectors of this wrapper-function
    SROppm_est_out = np.float32(OutputDXCPPhaT['SROppm_est_out'])
    TimeOffsetEndSeg_est_out = np.float32(OutputDXCPPhaT['TimeOffsetEndSeg_est_out'])

    # write output data into pipes
    outputData = np.array([SROppm_est_out, TimeOffsetEndSeg_est_out], dtype=np.float32)
    pipes[0].write(outputData)
    pipes[0].flush()

    if (int(args.record) == 1) and (Inst_DXCPPhaT.ell_sigSec <= NumSegs_toSave):
        if Inst_DXCPPhaT.ell_inSigSec == 1:  # only once in the beginning
            frames = inputData
        else:
            frames = np.concatenate((frames, inputData))
        # save stereo signal of the last segment
        if (Inst_DXCPPhaT.ell_sigSec == 3) and (Inst_DXCPPhaT.ell_inSigSec == ResetPeriod_NumFr + 1) and (flagSave == 1):
            WavOutput_FolderName = '/home/asn/asn_daemon/logfiles/'
            WavOutput_FileName = 'AsyncAudio2x1ch_' + str(Inst_DXCPPhaT.ell_sigSec) + 'sigSegs.wav'
            write(WavOutput_FolderName + WavOutput_FileName, RefSampRate_fs_Hz, frames)
            flagSave = 0
            #print('... ' + WavOutput_FileName + ' is saved for ell_inSigSec = ' + str(Inst_DXCPPhaT.ell_inSigSec))
            print('... ' + WavOutput_FileName + ' is saved :-)')
            sys.stdout.flush()