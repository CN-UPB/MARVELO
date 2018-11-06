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
from asntoolbox import Reframe

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                            action="append")
    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")

    return parser.parse_args()

args = parse_arguments()


''' Read module'''

# #print "output pipes " , args.outputs
# PACKETSIZE = 4096 #send data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)
#
# #read complete file using scipy
# print("begin reading audio file")
# sys.stdout.flush()
#
# sampleRate, data = scipy.io.wavfile.read('/home/hafifi/Desktop/docPaderborn/asnRepo/p1/Testbench/asn_server_Emulator/asn_server/Testbench/system/readfile_module/AudioData/Audio_2Chan_80ppm.wav')
#
# data = data.copy(order ='C')
# dataLength, dataChannels = data.shape
# sampleSize = data.itemsize
# dataSize = dataLength * dataChannels * sampleSize
#
# #print some information about the file
# print("file read successfully:\n -sampleRate = %d samples/sec\n -sampleSize = %d bytes\n -bitrate per channel = %d kb/s\n -\
# dataLength = %d samples\n -dataChannels = %d channels\n -dataSize = %d KiB\n -duration = %f sec"\
# %(sampleRate, sampleSize, sampleRate*sampleSize*8/1000, dataLength, dataChannels, dataSize/1024, dataLength/sampleRate))
# sys.stdout.flush()

###################################
##################################
#################################

print "Entered Module"
PACKETSIZE = 4096 #receive data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)

#init parameters for algorithms (these are not set as commandline arguments!)
vad_params = {"EnergySmoothFactor": 0.9, "OvershootFactor": 2.0}
psd_params = {"FFTSize": 8192, "WelchShift": 1024, "WindowType": "Hann"}
delay_params = {"FrameSize": 40960, "Delay": 1024}
cw_params = {"FFTSize": 8192, "CoherenceTimeDelay": 1024, "MaximumSRO": 300, "WelchShift": 1024}
resampling_params1 = {"SamplingRateOffset": 0, "WindowSize": 10, "FrameSize": 1024}
resampling_params2 = {"SamplingRateOffset": 0, "WindowSize": 10, "FrameSize": 1024}
rescontrol_params = {"SmoothFactor": 0.9, "UpdateAfterNumObservations": 30}
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


'''>>>>>>>>>>>>>>>>>>>>>>> Pipes <<<<<<<<<<<<<<<<<<<'''

##open input pipe
input1 = os.fdopen(int(args.input[0]), 'rb')
input2 = os.fdopen(int(args.input[1]), 'rb')
frame1 = np.fromfile(input1, dtype='i2', count=PACKETSIZE/4) #item size is 2 bytes!
frame2 = np.fromfile(input2, dtype='i2', count=PACKETSIZE/4) #item size is 2 bytes!
print 'read first packet'
#rate, frame = scipy.io.wavfile.read('/home/hafifi/Desktop/docPaderborn/asnRepo/p1/Testbench/asn_server_Emulator/asn_server/Testbench/system/readfile_module/AudioData/Audio_2Chan_80ppm.wav')
#packet = data[0:1024, :]
packet = np.c_[frame1[0:1024],frame2[0:1024]]
#open logfiles
#logfiles = [open(f, 'w') for f in args.logfiles]

packetCount = 1
blockCount = 0

print("ready for first data")
sys.stdout.flush()
#assembling first 160KB data block
#packet = frame1[0:2048] # np.fromfile(input, dtype='i2', count=2048) #item size is 2 bytes!
print 'packet.size = ', packet.size
print 'PACKETSIZE/2 = ', PACKETSIZE/2

#loop while data is still coming in -> last packet is skipped because it is not complete
while packet.size == PACKETSIZE/2 and blockCount <20:

    #shift frame 2048 items forward (4096 bytes - 1024 samples/channel) using next packet
    #if blockCount != 0:
    #    frame = frame[2048:]
    #    frame = np.append(frame, packet)

    DataBlock = np.reshape(packet, (PACKETSIZE/4, 2)) # packet
    # packet1 = DataBlock[:,0]
    # packet2 = DataBlock[:,1]

    # Resampling of streams
    # DataBlock1 = Resampling_Block1.process_data(packet1)
    # DataBlock2 = Resampling_Block2.process_data(packet2)

    DataBlock1 = DataBlock[:,0]
    DataBlock2 = DataBlock[:,1]
    #DataBlock2 = Resampling_Block2.process_data(DataBlock[:,0])


    # # Reframing of data
    # DataBlock1_RF = Reframe_Block1.process_data(DataBlock1['value'])
    # DataBlock2_RF = Reframe_Block2.process_data(DataBlock2['value'])
    #
    #
    # # Delay element for second coherence function
    # delay_DataBlock1 = Delay_Block1.process_data(DataBlock1_RF['value'])
    # delay_DataBlock2 = Delay_Block2.process_data(DataBlock2_RF['value'])
    #
    #
    # # Coherence function
    # coherence1 = CW_Block1.process_data(DataBlock1_RF['value'], DataBlock2_RF['value'])
    # coherence2 = CW_Block2.process_data(delay_DataBlock1, delay_DataBlock2)
    #
    #
    # coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1['value'], coherence2['value'])
    #
    #
    # sro_info = ResamplingControl_Block.process_data(coherenceDrift['value'])
    # if sro_info['flag1']:
    #     Resampling_Block1.process_async_data(sro_info['value1'])
    # if sro_info['flag2']:
    #     Resampling_Block2.process_async_data(sro_info['value2'])
    #
    # #print/write output
    # print 'sro >>>> ' , sro_info['value2']
    #sys.stdout.flush()
    #for f in logfiles:
    #    f.write(str(sro_info['value']) + "\n")

    #read next packet from input
    frame1 = np.fromfile(input1, dtype='i2', count=PACKETSIZE/4)
    frame2 = np.fromfile(input2, dtype='i2', count=PACKETSIZE/4)
    #packet = data[0+packetCount*1024:1024+packetCount*1024, :]
    # p1 = frame[0+packetCount*PACKETSIZE/4:1024+packetCount*PACKETSIZE/4, :]

    #packet = frame[0+packetCount*PACKETSIZE/4:1024+packetCount*PACKETSIZE/4, :]
    packet = np.c_[frame1,frame2]
    packetCount += 1
    blockCount += 1

print("no more data - exiting*************")
sys.stdout.flush()

input1.close()
input2.close()
#close pipes/files
#input.close()
#for f in logfiles:
#    f.close()
