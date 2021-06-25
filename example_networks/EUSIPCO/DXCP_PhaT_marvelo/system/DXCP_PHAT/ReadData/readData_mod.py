#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np
#from scipy import io            # to load .mat file
from scipy.io import wavfile    # to read .wav file


def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    # parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    # parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()

print('Unit test of DXCP-PhaT starts processing...')
sys.stdout.flush()

sigLen_s = 120             # length of the input signal
SNRdB = 10                 # signal-to-noise-ratio
fileName = 'source_speech_noise_pink_T60_500ms_sigLen_' + str(sigLen_s) + 's_micDist_20cm_srcPos_1.5m_2.5m_snr_' + str(SNRdB) + 'dB'

# use .mat file to load data
#mat = io.loadmat('signals/' + fileName + '.mat')
#x = mat['x']  # (nr_samples x nr_channel)

# use .wav file to load data
_, data = wavfile.read('signals/' + fileName + '.wav')
data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
data_norm_max = np.max(np.abs(np.hstack((data_norm[:, 0], data_norm[:, 1]))))
x = data_norm.transpose()

# calculate
nr_samples, nr_channel = x.shape
FrameSize_input = 2**7      # frame size (power of 2) of input data (also FrameShift in demo JS)
sizeLoop = int(nr_samples/FrameSize_input) # nr_samples/frameSize

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
for pktCntr in range(sizeLoop):
    outputData = x[np.arange(pktCntr*128, (pktCntr+1)*128), :]
    outputData_0 = outputData[:, 0].copy(order='C')
    outputData_1 = outputData[:, 1].copy(order='C')
    pipes[0].write(outputData_0)
    pipes[1].write(outputData_1)


#     outputData[:, 0] = outputData_0
#     outputData[:, 1] = outputData_1
#     if not np.mod(pktCntr,100):
#         print(pktCntr,outputData)
#         sys.stdout.flush()
#     Inst_DXCPPhaTcl=DXCP_PhaT_CL_wrapper( RefSampRate_fs_Hz, FrameSize_input,outputData,pktCntr,Inst_DXCPPhaTcl)

#     pipes[0].flush()#
#     pipes[1].flush()  #  #   #print('write in readData', pktCntr)
#     sys.stdout.flush()
#
# #print('Done writing')

# for pipe in pipes:
#   pipe.close()# Close input pipe

