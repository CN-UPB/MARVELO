#!/usr/bin/env python3
import os
import argparse
import numpy as np
from scipy import signal
import scipy.io
import os,sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--sro", type=int, default=10)
    parser.add_argument("--rate", type=int, default=16000)
    parser.add_argument("--L", type=int, default=4)
    #parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
sro = args.sro
rate = args.rate
L=args.L

filter_fd = 7000
filter_fs = 8000
filter_len = 241
chunckSize=  4096

'''start'''
#inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
print ('will start reading in synchResampler')
sys.stdout.flush()

data_sync_total = []
for pktCntr in range(0, 246):
    data_syncc = [os.read(int(f), chunckSize*8 ) for f in args.inputs]
    data_sync = np.fromstring(data_syncc[0], dtype=np.float)
    data_sync_total=np.concatenate((data_sync_total,data_sync),axis=0)
    #print('read in synchresampler', pktCntr)
    #sys.stdout.flush()

#data_sync = np.fromfile(inputs[0], dtype=np.int, count=20000) #stream data
data_sync = np.reshape(data_sync_total,(-1,2))
print (data_sync.shape)
sys.stdout.flush()


#data_sync = np.load('AudioData/Audio_2Chan_' + str(sro) + 'ppm_sync.npy')

#B = signal.remez(filter_len, [0, filter_fd, filter_fs, rate/2*L], [1, 0], fs=L*rate)
mat = scipy.io.loadmat('MatFiles/firpm_B241.mat');
B_mat = mat['B'];
B_mat_tr = B_mat.transpose();
B = B_mat_tr[:,0]

data_new = np.zeros((L*data_sync.shape[0], 1))
data_new[::L, 0] = data_sync[:, 1]

data_new_reshaped = data_new.reshape((data_new.shape[0],))
data_interp = L*signal.lfilter(B, 1.0, data_new_reshaped)

#np.save('AudioData/Audio_2Chan_' + str(sro) + 'ppm_interp.npy', data_interp)
#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#outputs[0].write(data_interp)

## for i in inputs:
##     i.close()
print ('relative size ', data_interp.size/4096)
sys.stdout.flush()

data_interp=np.reshape(data_interp,(1,-1))
sys.stdout.flush()

##for pipe in inputs:
##    pipe.close()
'''end'''
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

maxpktNr = int(246*L/2)
print ('total pktNr = ', maxpktNr)
#data_interp = np.ones(246*2*4096)
for pktNr in range(maxpktNr):
    for pipe in pipes:
        pipe.write(data_interp[int(pktNr*(chunckSize)):int((1+pktNr)*chunckSize)])
        #print('write in synchResampler', pktNr)
        #sys.stdout.flush()
        pipe.flush()# Close output pipes

print ('********************Done Actual Synch**********************')

for pipe in pipes:
  pipe.close()# Close input pipe
