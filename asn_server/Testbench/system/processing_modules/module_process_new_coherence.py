#!/usr/bin/env python

import numpy as np
import os
import scipy.io.wavfile
from asntoolbox import Vad
from asntoolbox import CoherenceWelch
from asntoolbox import Delay
from asntoolbox import CoherenceDriftEstimator
from asntoolbox import Resampling
from asntoolbox import ResamplingControl
import argparse
import select
import time
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                        action="append" )
    parser.add_argument("--logfiles", "-l",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    return parser.parse_args()

args = parse_arguments()
# Parameters for vad, psd, ...
vad_params = {"EnergySmoothFactor": 0.9, "OvershootFactor": 2.0}
psd_params = {"FFTSize": 8192, "WelchShift": 1024, "WindowType": "Hann"}
delay_params = {"FrameSize": 1024, "Delay": 1024}
cw_params = {"FFTSize": 8192, "CoherenceTimeDelay": 1024, "MaximumSRO": 300, "WelchShift": 1024}
resampling_params = {"SamplingRateOffset": 0, "WindowSize": 20}
rescontrol_params = {"SmoothFactor": 0.99, "UpdateAfterNumObservations": 30}
smoothFac = 0.99

# Init Processing Blocks
# Vad_Block = Vad(vad_params)
# CW_Block1 = CoherenceWelch(psd_params)
# CW_Block2 = CoherenceWelch(psd_params)
# Delay_Block1 = Delay(delay_params)
# Delay_Block2 = Delay(delay_params)
#CoherenceDriftEstimator_Block = CoherenceDriftEstimator(cw_params)
# Resampling_Block = Resampling(resampling_params)
ResamplingControl_Block = ResamplingControl(rescontrol_params)

# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_40ppm.wav')
# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_10ppm.wav')
# rate, data = scipy.io.wavfile.read('/home/hafifi/Desktop/docPaderborn/asnRepo/p1/Testbench/asn_server_Emulator/asn_server/Testbench/system/readfile_module/AudioData/Audio_2Chan_80ppm.wav')
# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_100ppm.wav')
#
#
#logfiles = [open(f, 'w') for f in args.logfiles]
#timefile = open("/home/pi/asn_daemon/logfiles/moduleProccNewSampling.log","w")
print("ready for first data")
sys.stdout.flush()

input = [os.fdopen(int(f), 'rb') for f in args.input]
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

datalen=1024
#frame = np.fromfile(input[0], dtype='i2', count=datalen) #item size is 2 bytes

# Simulated Processing
# Mic1:DataBlock1 -> Vad_Block => vad_value
# Mic1:DataBlock1 -> PSD_Block1(1) => psd_value1 -> CoherenceDrift(1)
# Mic2:DataBlock2 -> PSD_Block2(1) => psd_value2 -> CoherenceDrift(2)
# CoherenceDrift => Resampling
n = 0
# dataLength, channels = data.shape
coEst = 0
packetLen = 1024
dataLength = packetLen
packetNr = 0
DataBlock1_buff = []
DataBlock2_buff = []
delay_DataBlock1_buf = []
delay_DataBlock2_buf = []
start= time.time()
# while packetNr < 40:
#     while 1:
#         r, w, e = select.select([int(args.input[0])], [], [], 1024)
#         DataBlock1=[]
#         if int(args.input[0]) in r:
#             DataBlock1 = np.fromfile(input[0], dtype='i2',
#                              count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
#             # #timefile.write('\nbuffer pktNr' + str(packetNr))
#             # #timefile.flush()
#             break
#         else:
#
#             pass
#             #print "nothing available from pipe 0!"  # or just ignore that case
#             #sys.stdout.flush()
#
#             #timefile.write('\nno buffer from pipe 0' )
#             #timefile.flush()
#     DataBlock1_buff = np.append(DataBlock1_buff, DataBlock1)
#     #DataBlock2_nosync = np.fromfile(input[1], dtype='i2',
#      #                               count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 0]
#
#     # ------ Sync Processing - DES ----------
#     # Resampling of second stream
#     while 1:
#         r, w, e = select.select([int(args.input[1])], [], [], 1024)
#         DataBlock2=[]
#         if int(args.input[1]) in r:
#             DataBlock2 = np.fromfile(input[1], dtype='i2',
#                              count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
#             if packetNr == 0:
#                 start = time.time()
#             #timefile.write('\nbuffer pktNr' + str(packetNr))
#             #timefile.flush()
#             break
#         else:
#             pass
#             #print "nothing available from pipe 1!"  # or just ignore that case
#             #sys.stdout.flush()
#
#             #timefile.write('\nnobuffer from pipe 1' )
#             #timefile.flush()
#
#
#     #DataBlock2 = np.fromfile(input[1], dtype='i2',
#     #                                count=datalen)
#     #Resampling_Block.process_data(DataBlock2_nosync)
#     DataBlock2_buff = np.append(DataBlock2_buff, DataBlock2)
#     # Delay some data
#     delay_DataBlock1 = np.fromfile(input[2], dtype='i2',
#                              count=datalen)#Delay_Block1.process_data(DataBlock1)
#     delay_DataBlock1_buf = np.append(delay_DataBlock1_buf, delay_DataBlock1)
#     delay_DataBlock2 = np.fromfile(input[3], dtype='i2',
#                              count=datalen)#Delay_Block2.process_data(DataBlock2)
#     delay_DataBlock2_buf = np.append(delay_DataBlock2_buf, delay_DataBlock2)
#     #timefile.write('\ncount pktNr'+str(packetNr))
#     #timefile.flush()
#     packetNr = packetNr + 1
#

while n < 505599 - 5 * 8192:
    # # Shift Data
    #
    # #timefile.write('\nstart shifting with n=' + str(n))
    # #timefile.flush()
    #
    # if n!=0:
    #     #timefile.write('\nstart appending with n=' + str(n))
    #     #timefile.flush()
    #
    #     while 1:
    #         #timefile.write('\nchecking pipe with n=' + str(n))
    #         #timefile.flush()
    #
    #         r, w, e = select.select([int(args.input[0])], [], [], 1024)
    #         #timefile.write('\nchecked pipe with n=' + str(n))
    #         #timefile.flush()
    #         DataBlock1 = []
    #         if int(args.input[0]) in r:
    #             DataBlock1 = np.fromfile(input[0], dtype='i2',
    #                                      count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
    #             break
    #         else:
    #             pass
    #             #print "nothing available from pipe 0!"  # or just ignore that case
    #             #sys.stdout.flush()
    #
    #             #timefile.write('\nothing available from pipe 0!=' + str(n))
    #             #timefile.flush()
    #
    #     #DataBlock1 = np.fromfile(input[1], dtype='i2',
    #     #                         count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
    #     DataBlock1_buff = np.append(DataBlock1_buff[datalen:], DataBlock1)
    #     #DataBlock2_nosync = np.fromfile(input[0], dtype='i2',
    #     #                                count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 0]
    #
    #     # ------ Sync Processing - DES ----------
    #     # Resampling of second stream
    #     while 1:
    #         r, w, e = select.select([int(args.input[1])], [], [], 1024)
    #         DataBlock2 = []
    #         if int(args.input[1]) in r:
    #             DataBlock2 = np.fromfile(input[1], dtype='i2',
    #                                      count=datalen)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
    #
    #             break
    #         else:
    #             pass
    #             #print "nothing available from pipe 1!"  # or just ignore that case
    #             #sys.stdout.flush()
    #
    #     #DataBlock2 = np.fromfile(input[1], dtype='i2',
    #     #                            count=datalen)#Resampling_Block.process_data(DataBlock2_nosync)
    #     DataBlock2_buff = np.append(DataBlock2_buff[datalen:], DataBlock2)
    #     # Delay some data
    #     delay_DataBlock1 = np.fromfile(input[2], dtype='i2',
    #                          count=datalen)#Delay_Block1.process_data(DataBlock1)
    #     delay_DataBlock1_buf = np.append(delay_DataBlock1_buf[datalen:], delay_DataBlock1)
    #     delay_DataBlock2 = np.fromfile(input[3], dtype='i2',
    #                          count=datalen)#Delay_Block2.process_data(DataBlock2)
    #     delay_DataBlock2_buf = np.append(delay_DataBlock2_buf[datalen:], delay_DataBlock2)
    #

    # DataBlock1_buff = np.fromfile(input[0], dtype='i2', count=40960)
    # DataBlock2_buff= np.fromfile(input[1], dtype='i2', count=40960)
    # delay_DataBlock1_buf= np.fromfile(input[2], dtype='i2', count=40960)
    # delay_DataBlock2_buf= np.fromfile(input[3], dtype='i2', count=40960)
    #print 'diff1', sum(DataBlock1_buff-DataBlock2_buff)
    # sys.stdout.flush()

    # Calc: Coherence via Welch
    # coherence1 = np.fromfile(input[0], dtype='i2', count=8192)# CW_Block1.process_data(DataBlock1_buff, DataBlock2_buff)
    # # Calc: Coherence via Welch (delayed data)
    # coherence2 = np.fromfile(input[1], dtype='i2', count=8192)#CW_Block2.process_data(delay_DataBlock1_buf, delay_DataBlock2_buf)
    # coherence22 =CW_Block2.process_data(delay_DataBlock1_buf, delay_DataBlock2_buf)
    #print 'coherence diff = ', sum(coherence2-coherence22)
    #sys.stdout.flush()

    # Calc: Coherence Drift
    coherenceDrift =  np.fromfile(input[0],  dtype=np.float64, count=1)#CoherenceDriftEstimator_Block.process_data(coherence1, coherence2)
    #print 'len coherence welch1 = ', len(coherence1)
    #print 'len coherence welch2 = ', len(coherence2)

    sys.stdout.flush()
    # hand over to control block
    sro_info = ResamplingControl_Block.process_data(coherenceDrift[0])
    if sro_info['value']!=sro_info['value']:
        sro_info['value'] = -1
    else:
        print 'sroValue >>> ',sro_info['value']
        sys.stdout.flush()

    for pipe in outputs:
        pipe.write(str(sro_info)+ '\n')
        #timefile.write('\nwrote sro info' + str(sro_info))
        #timefile.flush()
        pipe.flush()
    # #  ---- Asncy Communication handling ----
    # if sro_info['flag'] == True:
    #     Resampling_Block.process_async_data(sro_info['value'])

    #print(sro_info['value'])
    #sys.stdout.flush()

    n += 1024
    packetNr = packetNr + 1
    #print packetNr
    #sys.stdout.flush()

    if packetNr == 400:
        print 'end time at 400: ', time.time()
        print 'time elapsed --> ', time.time() - start

        sys.stdout.flush()
# print 'time elapsed --> ', time.time()-start
# sys.stdout.flush()

print 'done'
sys.stdout.flush()
