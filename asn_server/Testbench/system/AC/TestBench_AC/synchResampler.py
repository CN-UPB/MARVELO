#import os
#import argparse
import numpy as np
from scipy import signal

#def parse_arguments():
#    parser = argparse.ArgumentParser(description='arguments')
#    parser.add_argument("--inputs", "-i",  action="append")
#    parser.add_argument("--outputs", "-o", action="append")
#    parser.add_argument("--FFTSize", type=int, default=8192)
#    parser.add_argument("--logfiles", "-l", action="append")
#    return parser.parse_args()

#args = parse_arguments()
sro = 10
rate = 16000

L=4
filter_fd = 7000
filter_fs = 8000
filter_len = 241

# inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
# data = np.fromfile(inputs[0], dtype='i2', count=40960) #stream data
data_sync = np.load('AudioData/Audio_2Chan_' + str(sro) + 'ppm_sync.npy')

B = signal.remez(filter_len, [0, filter_fd, filter_fs, rate/2*L], [1, 0], fs=L*rate)

data_new = np.zeros((L*data_sync.shape[0], 1))
data_new[::L, 0] = data_sync[:, 1]

data_new_reshaped = data_new.reshape((data_new.shape[0],))
data_interp = L*signal.lfilter(B, 1.0, data_new_reshaped)

np.save('AudioData/Audio_2Chan_' + str(sro) + 'ppm_interp.npy', data_interp)
#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#outputs[0].write(data_interp)