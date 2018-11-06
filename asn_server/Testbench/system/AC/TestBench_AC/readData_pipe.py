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
    parser.add_argument("--sro", type=int, default=10,  action="append")
    parser.add_argument("--delay_int_chan", type=int, default=-252,  action="append")
    #parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
sro = args.sro
delay_int_chan = args.delay_int_chan
chunkSize = 4096
#inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
# data = np.fromfile(inputs[0], dtype='i2', count=40960) #stream data
rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_' + str(sro) + 'ppm.wav')
#data = data[0:4096*246]  # cutting data if necessary
print('total nr pkts=', data.size/chunkSize)
sys.stdout.flush()


data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
data_norm = data_norm.transpose()

data_sync = np.vstack((data_norm[(-delay_int_chan-1):, 0], data_norm[0:(data.shape[0]+delay_int_chan+1), 1]))
data_sync = data_sync.transpose()

#np.save('AudioData/Audio_2Chan_' + str(sro) + 'ppm_sync.npy', data_sync)
#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#outputs[0].write(data_sync)

#for pipe in inputs:
#    pipe.close()

#for pipe in outputs:
#    pipe.close()

#inputs.close()

pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]
data_sync = np.reshape(data_sync,(1,-1))
for pipe in pipes:
 for pktCntr in range(0, 246):
  data_sync = data_sync.copy(order='C')
  pipe.write(data_sync[pktCntr:(1+pktCntr)*chunkSize])
  pipe.flush()#
  #print('write in readData', pktCntr)
  sys.stdout.flush()

#print('Done writing')

for pipe in pipes:
  pipe.close()# Close input pipe

