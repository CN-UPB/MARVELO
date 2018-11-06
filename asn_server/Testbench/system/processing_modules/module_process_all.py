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
import time
start = time.time()


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--logfiles", "-l",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
#print "input pipes ",args.input
PACKETSIZE = 4096 #receive data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)

#init parameters for algorithms (these are not set as commandline arguments!)
vad_params = {"EnergySmoothFactor": 0.9, "OvershootFactor": 2.0}
psd_params = {"FFTSize": 8192, "WelchShift": 1024, "WindowType": "Hann"}
delay_params = {"FrameSize": 40960, "Delay": 1024}
cw_params = {"FFTSize": 8192, "CoherenceTimeDelay": 1024, "MaximumSRO": 300, "WelchShift": 1024}
resampling_params = {"SamplingRateOffset": 0, "WindowSize": 20}
rescontrol_params = {"SmoothFactor": 0.99, "UpdateAfterNumObservations": 30}
smoothFac = 0.99

#init processing blocks
Vad_Block = Vad(vad_params)
CW_Block1 = CoherenceWelch(psd_params)
CW_Block2 = CoherenceWelch(psd_params)
Delay_Block1 = Delay(delay_params)
Delay_Block2 = Delay(delay_params)
CoherenceDriftEstimator_Block = CoherenceDriftEstimator(cw_params)
Resampling_Block = Resampling(resampling_params)
ResamplingControl_Block = ResamplingControl(rescontrol_params)

#open input pipe

#open logfiles
logfiles = [open(f, 'w') for f in args.logfiles]
timefile = open("/home/asn/asn_daemon/logfiles/time.log","w") 



sys.stdout.flush()
#assembling first 160KB data block
#open input pipe
input = os.fdopen(int(args.input), 'rb')

packetCount = 1
blockCount = 0

print("ready for first data")
#print("ready for first data--<",input,int(PACKETSIZE/2))
sys.stdout.flush()
#assembling first 160KB (40960 samples) data block
print('------------',PACKETSIZE/2)
datalen = int(PACKETSIZE/2)
frame = np.fromfile(input, dtype='i2', count=datalen) #item size is 2 bytes


while packetCount <  40:
    packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2)
    frame = np.append(frame, packet)
    packetCount += 1
print("first block of 40960 samples received")
sys.stdout.flush()
print("start processing data from buffer (1024 samples offset")
sys.stdout.flush()
#loop while data is still coming in -> last packet is skipped because it is not complete
while packet.size == PACKETSIZE/2:

    #shift frame 2048 items forward (4096 bytes - 1024 samples/channel) using next packet
    if blockCount != 0:
        frame = frame[2048:]
        frame = np.append(frame, packet)

    #make copy of frame (in case processing changes this data)
    DataBlock = frame.copy()

    #reshape frame to prepare channel seperation
    DataBlock = np.reshape(DataBlock, (40960, 2))

    #seperate channels for processing
    DataBlock1 = DataBlock[:, 1]
    DataBlock2_nosync = DataBlock[:, 0]

    # ------ Sync Processing - DES ----------
    # Resampling of second stream
    DataBlock2 = Resampling_Block.process_data(DataBlock2_nosync)
    # Process VAD
    vad_value = Vad_Block.process_data(DataBlock1)
    # Calc: Coherence via Welch
    coherence1 = CW_Block1.process_data(DataBlock1, DataBlock2)
    # Delay some data
    delay_DataBlock1 = Delay_Block1.process_data(DataBlock1)
    delay_DataBlock2 = Delay_Block2.process_data(DataBlock2)
    # Calc: Coherence via Welch (delayed data)
    coherence2 = CW_Block2.process_data(delay_DataBlock1, delay_DataBlock2)
    # Calc: Coherence Drift
    coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1, coherence2)
    # hand over to control block
    sro_info = ResamplingControl_Block.process_data(coherenceDrift)

    #  ---- Asncy Communication handling ----
    if sro_info['flag'] == True:
        Resampling_Block.process_async_data(sro_info['value'])

    #print/write output
    print(sro_info['value'])
    end = time.time()
    timeElapsed = (end - start)
    print('elapsed-->',timeElapsed )
    timefile.write(str(timeElapsed)+ '\n')
    timefile.flush()

    sys.stdout.flush()
    for f in logfiles:
        f.write(str(sro_info['value']) + "\n")

    #read next packet from input
    packet = np.fromfile(input, dtype='i2', count=int(PACKETSIZE/2))
    packetCount += 1
    blockCount += 1

print("no more data - exiting")
timeElapsed = (end - start)
print ('elapsed-->'+str(timeElapsed) )
timefile.write(str(timeElapsed)+'\n')
timefile.flush()
timefile.close()
sys.stdout.flush()
#close pipes/files
input.close()
for f in logfiles:
    f.close()
