#import os
#import argparse
import numpy as np
import scipy.io.wavfile
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
delay_int_chan = -252

# inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
# data = np.fromfile(inputs[0], dtype='i2', count=40960) #stream data
rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_' + str(sro) + 'ppm.wav')

data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
data_norm = data_norm.transpose()

data_sync = np.vstack((data_norm[(-delay_int_chan-1):, 0], data_norm[0:(data.shape[0]+delay_int_chan+1), 1]))
data_sync = data_sync.transpose()

np.save('AudioData/Audio_2Chan_' + str(sro) + 'ppm_sync.npy', data_sync)
#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#outputs[0].write(data_interp)