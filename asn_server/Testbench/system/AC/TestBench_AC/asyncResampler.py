#import os
#import argparse
import numpy as np

#def parse_arguments():
#    parser = argparse.ArgumentParser(description='arguments')
#    parser.add_argument("--inputs", "-i",  action="append")
#    parser.add_argument("--outputs", "-o", action="append")
#    parser.add_argument("--FFTSize", type=int, default=8192)
#    parser.add_argument("--logfiles", "-l", action="append")
#    return parser.parse_args()

#args = parse_arguments()
rate = 16000
sro = 10
eps = sro/1000000
Fs_offset = rate*(1+eps)
L=4

#inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
#data_interp = np.fromfile(inputs[0], dtype='i2', count=40960) #stream data
data_interp = np.load('AudioData/Audio_2Chan_' + str(sro) + 'ppm_interp.npy')
data_sync = np.load('AudioData/Audio_2Chan_' + str(sro) + 'ppm_sync.npy')

#exec(open("/home/chinaev/Desktop/RUB/GITs/ASN_P2a/TestBench_AC/aFIFImODULE/synchResampler.py").read())
#rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_' + str(sro) + 'ppm.wav')

data_resampled = np.zeros((data_sync.shape[0], 1))
for p in range(data_sync.shape[0]-1):
    p_punkt = int(np.floor(4 * p * Fs_offset / rate))
    nue = 4 * p * (1 + eps) - p_punkt
    beta_1 = -(nue * (nue - 1) * (nue - 2)) / 6
    beta0 = ((nue + 1) * (nue - 1) * (nue - 2)) / 2
    beta1 = -((nue + 1) * nue * (nue - 2)) / 2
    beta2 = ((nue + 1) * nue * (nue - 1)) / 6
    if p_punkt != 0 and p_punkt <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta_1 * data_interp[p_punkt]
    if p_punkt+1 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta0 * data_interp[p_punkt+1]
    if p_punkt+2 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta1 * data_interp[p_punkt+2]
    if p_punkt+3 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta2 * data_interp[p_punkt+3]

# region... evaluate upsampling by using SINR measure
filter_len = 241

delay_res = int((filter_len - 1) / 2 / L)
data_eval = data_sync[0:(data_sync.shape[0] - delay_res + 1), :]
data_resampled_eval = data_resampled[(delay_res - 1):, 0]

PowerRef = np.mean(data_eval[:, 0] ** 2)
InterpolNoise = data_eval[:, 0] - data_eval[:, 1]
PowerNoise = np.mean(InterpolNoise ** 2)
sinr_in_dB = 10 * np.log10(PowerRef / PowerNoise)

InterpolNoise = data_eval[:, 0] - data_resampled_eval[:]
PowerNoise = np.mean(InterpolNoise ** 2)
sinr_res_dB = 10 * np.log10(PowerRef / PowerNoise)
print(sinr_in_dB, sinr_res_dB)

#outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#outputs[0].write(DataResult)
#for f in logfiles:
#    f.write(someData + "\n")