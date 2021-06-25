#!/usr/bin/env python3
import os
import sys
import wave
import pyaudio
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
    parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
if (int(args.mode) == 1) or (int(args.mode) == 3):
    inputDataType = 'int16'
if int(args.mode) == 2:
    inputDataType = 'float32'
print('... parameters of DXCP-PhaT are set in: ' + args.config_file + '; with input data type: ' + inputDataType + ' ...')
sys.stdout.flush()

# call constructor of DXCP-PhaT
Inst_DXCPPhaT = DXCPPhaT()

#FrameSize_input = 128
inputData = np.zeros((FrameSize_input, 2))
if (int(args.mode) == 1) or (int(args.mode) == 3):
    reader1 = PipeReader(int(args.inputs[0]), (int(FrameSize_input), int(1)), np.int16)
    reader2 = PipeReader(int(args.inputs[1]), (int(FrameSize_input), int(1)), np.int16)
if int(args.mode) == 2:
    reader1 = PipeReader(int(args.inputs[0]), (int(FrameSize_input), int(1)), np.float32)
    reader2 = PipeReader(int(args.inputs[1]), (int(FrameSize_input), int(1)), np.float32)
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

# main loop
if (int(args.mode) == 1) or (int(args.mode) == 2):
    while True:
        # get input data from pipes
        inputData[:, 0] = reader1.read_block()[:, 0]
        inputData[:, 1] = reader2.read_block()[:, 0]

        # execute DXCP-PhaT for one data frame inputData = x_12_ell
        OutputDXCPPhaT = Inst_DXCPPhaT.process_data(inputData)

        # set output vectors of this wrapper-function
        SROppm_est_out = np.float32(OutputDXCPPhaT['SROppm_est_out'])
        TimeOffsetEndSeg_est_out = np.float32(OutputDXCPPhaT['TimeOffsetEndSeg_est_out'])

        # write output data into pipes
        outputData = np.array([SROppm_est_out, TimeOffsetEndSeg_est_out], dtype=np.float32)
        pipes[0].write(outputData[0])
        pipes[1].write(outputData[1])
        pipes[0].flush()
        pipes[1].flush()

if int(args.mode) == 3:
    RESPEAKER_RATE = 16000
    RECORD_SECONDS = 65
    WAVE_OUTPUT_FILENAME = "/home/asn/asn_daemon/logfiles/output2"

    RESPEAKER_CHANNELS = 1
    RESPEAKER_WIDTH = 2
    # main loop
    #frames = []
    # text_file = open("/home/asn/asn_daemon/logfiles/output.txt", "w")
    # audiofile = open(WAVE_OUTPUT_FILENAME, "w")
    for i in range(0, int(RESPEAKER_RATE * RECORD_SECONDS / FrameSize_input)):
        # get input data from pipes
        inputData[:, 0] = reader1.read_block()[:, 0]
        inputData[:, 1] = reader2.read_block()[:, 0]
        if i == 1:
            print('... erster Wert: ' + str(inputData[0, 0]) + ' ... dtype: ' + str(inputData[0, 0].dtype))
            sys.stdout.flush()

        # write data
        #print('write %d' % i)
        #sys.stdout.flush()
        #frames.append(inputData[:, 0])
        #frames = np.append(frames,inputData[:, 0])
        #frames = frames + list(np.reshape(inputData[:, 0],(1,-1)))
        #frames = frames + list(inputData[:, 0][:])
        #print('... frames len: ', len(frames),' ...')
        #sys.stdout.flush()
        # text_file.write(str(inputData[:, 0]) + '\n')
        # audiofile.write(np.array2string(inputData[:, 0]))

        # execute DXCP-PhaT for one data frame inputData = x_12_ell
        OutputDXCPPhaT = Inst_DXCPPhaT.process_data(inputData)

        # set output vectors of this wrapper-function
        SROppm_est_out = np.float32(OutputDXCPPhaT['SROppm_est_out'])
        TimeOffsetEndSeg_est_out = np.float32(OutputDXCPPhaT['TimeOffsetEndSeg_est_out'])

        # write output data into pipes
        outputData = np.array([SROppm_est_out, TimeOffsetEndSeg_est_out], dtype=np.float32)
        pipes[0].write(outputData[0])
        pipes[1].write(outputData[1])
        pipes[0].flush()
        pipes[1].flush()

    # wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    # wf.setnchannels(RESPEAKER_CHANNELS)
    # wf.setsampwidth(RESPEAKER_WIDTH)
    # wf.setframerate(RESPEAKER_RATE)
    # wf.writeframes(''.join(frames.tobytes()))
    # wf.close()
    # text_file.close()
    # audiofile.close()
    # print('Done recording')
    # sys.stdout.flush()

    #frames = np.array(frames)
    #print('frames.shape[0]: ' + str(frames.shape[0]) + ', frames.shape[1]: ' + str(frames.shape[1]))
    #sys.stdout.flush()
    #frResh = np.int16(np.reshape(frames, (-1, 1)))
    #print('frResh.shape[0]: ' + str(frResh.shape[0]) + ', frResh.shape[1]: ' + str(frResh.shape[1]) + ', frResh.dtype: ' + str(frResh.dtype))
    #sys.stdout.flush()
    #write(WAVE_OUTPUT_FILENAME, RESPEAKER_RATE, frResh)
    #print("* recording done")
    #sys.stdout.flush()