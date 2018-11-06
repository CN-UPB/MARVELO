#!/usr/bin/env python

import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import Vad
from asntoolbox import CoherenceWelch
from asntoolbox import Delay
from asntoolbox import CoherenceDriftEstimator
from asntoolbox import Resampling
from asntoolbox import ResamplingControl

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--logfiles", "-l",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
print "input pipes ",args.input
PACKETSIZE = 4096 #receive data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)

#init parameters for algorithms (these are not set as commandline arguments!)
vad_params = {"EnergySmoothFactor": 0.9, "OvershootFactor": 2.0}
psd_params = {"FFTSize": 8192, "WelchShift": 1024, "WindowType": "Hann"}
delay_params = {"FrameSize": 40960, "Delay": 1024}
cw_params = {"FFTSize": 8192, "CoherenceTimeDelay": 1024, "MaximumSRO": 300, "WelchShift": 1024}
resampling_params1 = {"SamplingRateOffset": 0, "WindowSize": 15, "FrameSize": 1024}
resampling_params2 = {"SamplingRateOffset": 0, "WindowSize": 15, "FrameSize": 1024}
rescontrol_params = {"SmoothFactor": 0.9, "UpdateAfterNumObservations": 100}
reframe_params = {"InFrameSize": 1024, "OutFrameSize": 40960, "FrameShift": 1024}
smoothFac = 0.99

#init processing blocks
Vad_Block = Vad(vad_params, "VAD CH1")
Reframe_Block1 = Reframe(reframe_params, "Reframing Ch1")
Reframe_Block2 = Reframe(reframe_params, "Reframing Ch2")

CW_Block1 = CoherenceWelch(psd_params, "Coherence Welch 1")
CW_Block2 = CoherenceWelch(psd_params, "Coherence Welch 2")
Delay_Block1 = Delay(delay_params, "Delay 1")
Delay_Block2 = Delay(delay_params, "Delay 2")
CoherenceDriftEstimator_Block = CoherenceDriftEstimator(cw_params, "Drift Estimator")
Resampling_Block1 = Resampling(resampling_params1, "Resampling CH1")
Resampling_Block2 = Resampling(resampling_params2, "Resampling CH2")
ResamplingControl_Block = ResamplingControl(rescontrol_params, "Reample Control")

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open logfiles
logfiles = [open(f, 'w') for f in args.logfiles]

packetCount = 1
blockCount = 0

print("ready for first data")
sys.stdout.flush()
#assembling first 160KB data block
packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2) #item size is 2 bytes!
#while packetCount <  40:
#    packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2)
#    frame = np.append(frame, packet)
#    packetCount += 1
#print("first block of 40960 samples received")
#sys.stdout.flush()
#print("start processing data from buffer (1024 samples offset")
#sys.stdout.flush()
#loop while data is still coming in -> last packet is skipped because it is not complete
while packet.size == PACKETSIZE/2:

    #shift frame 2048 items forward (4096 bytes - 1024 samples/channel) using next packet
    #if blockCount != 0:
    #    frame = frame[2048:]
    #    frame = np.append(frame, packet)

    DataBlock = np.reshape(packet, (1024, 2))

    # Resampling of streams
    DataBlock1 = Resampling_Block1.process_data(DataBlock[:,0])
    DataBlock2 = Resampling_Block2.process_data(DataBlock[:,1])


    # Reframing of data
    DataBlock1_RF = Reframe_Block1.process_data(DataBlock1['value'])
    DataBlock2_RF = Reframe_Block2.process_data(DataBlock2['value'])


    # Delay element for second coherence function
    delay_DataBlock1 = Delay_Block1.process_data(DataBlock1_RF['value'])
    delay_DataBlock2 = Delay_Block2.process_data(DataBlock2_RF['value'])


    # Coherence function
    coherence1 = CW_Block1.process_data(DataBlock1_RF['value'], DataBlock2_RF['value'])
    coherence2 = CW_Block2.process_data(delay_DataBlock1['value'], delay_DataBlock2['value'])


    coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1['value'], coherence2['value'])


    sro_info = ResamplingControl_Block.process_data(coherenceDrift['value'])
    if sro_info['flag1']:
        Resampling_Block1.process_async_data(sro_info['value1'])
    if sro_info['flag2']:
        Resampling_Block2.process_async_data(sro_info['value2'])

    #print/write output
    print(sro_info['value'])
    sys.stdout.flush()
    for f in logfiles:
        f.write(str(sro_info['value']) + "\n")

    #read next packet from input
    packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2)
    packetCount += 1
    blockCount += 1

print("no more data - exiting")
sys.stdout.flush()
#close pipes/files
input.close()
for f in logfiles:
    f.close()
