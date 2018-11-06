#!/usr/bin/env python3
import os, sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy import signal

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    #parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--sro", type=int, default=100,  action="append")
    parser.add_argument("--delay_int_chan", type=int, default=-252,  action="append")
    #parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
sro = args.sro
delay_int_chan = args.delay_int_chan
chunkSize = 1000
#sro = 100 #  SINR_in = -2.581906 dB, SINR_out = 35.849048 dB
rate, data = scipy.io.wavfile.read('AudioData/Exp_1_FS_50_FE_6500_Length_30_BaseFreq_16000_SRO_' + str(sro) + '.wav')

sigLen_s = 10
data = data[0:(sigLen_s*rate)]  # cutting data if necessary

data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
data_norm_max = np.max(np.abs(np.hstack((data_norm[:, 0], data_norm[:, 1]))))
data_norm = data_norm.transpose()

data_toSend = np.reshape(data_norm,(1,-1))

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
for pipe in pipes:
 for pktCntr in range(0, 320):
  data_toSend = data_toSend.copy(order='C')
  pipe.write(data_toSend[pktCntr*chunkSize:(1+pktCntr)*chunkSize])
  pipe.flush()#
  #print('write in readData', pktCntr)
  sys.stdout.flush()

#print('Done writing')

for pipe in pipes:
  pipe.close()# Close input pipe

