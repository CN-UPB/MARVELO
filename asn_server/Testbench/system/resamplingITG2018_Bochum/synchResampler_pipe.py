#!/usr/bin/env python3
import os
import argparse
import numpy as np
from scipy import signal
import scipy.io
import os,sys
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--inputs", "-i",  action="append")
    parser.add_argument("--outputs", "-o", action="append")
    parser.add_argument("--sro", type=int, default=100)
    parser.add_argument("--rate", type=int, default=16000)
    parser.add_argument("--L", type=int, default=8)
    #parser.add_argument("--logfiles", "-l", action="append")
    return parser.parse_args()
args = parse_arguments()
sro = args.sro
rate = args.rate
L=args.L

filter_fd = 7000
filter_fs = 8000
filter_len = 797
chunckSize=  1000
sigLen_s = 10
'''start'''
#inputs = [os.fdopen(int(f), 'rb') for f in args.inputs]
print ('will start reading in synchResampler')
sys.stdout.flush()

data_sync_total = []
for pktCntr in range(0, 320):
    data_syncc = [os.read(int(f), chunckSize*8 ) for f in args.inputs]
    data_sync = np.fromstring(data_syncc[0], dtype=np.float)
    data_sync_total=np.concatenate((data_sync_total,data_sync),axis=0)
    #print('read in synchresampler', pktCntr)
    #sys.stdout.flush()

#data_sync = np.fromfile(inputs[0], dtype=np.int, count=20000) #stream data
data_sync = np.reshape(data_sync_total,(-1,2))
print (data_sync.shape)
#sys.stdout.flush()
data_norm = data_sync

print ('********************Done reading**********************')
#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_norm[:, 0], label='Mic-1')
#ax1.plot(data_norm[:, 1], linestyle=':', label='Mic-2')
#plt.legend(); plt.show()

print('\nSampling rate offset (SRO): %4.2fppm' % sro)
# endregion

# region... 2. Initialize the composite approach for asynchronous resampling
L=8; filter_len = 797
# filter_fd = 7000; filter_fs = 8000
#B = signal.remez(filter_len, [0, filter_fd, filter_fs, rate/2*L], [1, 0], fs=L*rate)
mat = scipy.io.loadmat('MatFiles/firpm_B797.mat'); B_mat = mat['B']; B_mat_tr = B_mat.transpose(); B = B_mat_tr[:,0]

#freq, response = signal.freqz(B)
#plt.plot(0.5*rate*freq/np.pi, 20*np.log10(np.abs(response)), 'b-')
#plt.grid(alpha=0.25); plt.xlabel('Frequency (Hz)'); plt.ylabel('Gain'); plt.show()
# endregion

# region... 3. Perform asynchronous resampling by applying the conventional composite approach
print('Perform asynchronous resampling by applying the conventional composite-resampling...')
time_start = time.time()
data_new = np.zeros((L*data_norm.shape[0], 1))
data_new[::L, 0] = data_norm[:, 1]

data_new_reshaped = data_new.reshape((data_new.shape[0],))
data_interp = L*signal.lfilter(B, 1.0, data_new_reshaped)

#delay_filt = int((filter_len-1)/2+1)
#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_new_reshaped[0:(data_new_reshaped.shape[0]-delay_filt)], label='data-new')
#ax1.plot(data_interp[delay_filt:], label='interpol')
#plt.legend(); plt.show()

delay_filtData = (filter_len-1)/2
delay_vec = L*(1+sro*1e-6)*np.arange(data_norm.shape[0],)+delay_filtData
data_res = np.zeros((data_norm.shape[0], 1))
for p in range(data_norm.shape[0]):
    #delay_akt1 = L * (1+sro*1e-6) * p
    delay_akt = delay_vec[p]
    p_punkt = np.int(np.floor(delay_akt))
    nue = delay_akt - p_punkt

    beta_1 = -(nue * (nue - 1) * (nue - 2)) / 6
    beta0 = ((nue + 1) * (nue - 1) * (nue - 2)) / 2
    beta1 = -((nue + 1) * nue * (nue - 2)) / 2
    beta2 = ((nue + 1) * nue * (nue - 1)) / 6

    if p_punkt != 0 and p_punkt <= data_interp.shape[0]-1:
        data_res[p] = data_res[p] + beta_1 * data_interp[p_punkt-1]
    if p_punkt != 0 and p_punkt+1 <= data_interp.shape[0]-1:
        data_res[p] = data_res[p] + beta0 * data_interp[p_punkt]
    if p_punkt+2 <= data_interp.shape[0]-1:
        data_res[p] = data_res[p] + beta1 * data_interp[p_punkt+1]
    if p_punkt+3 <= data_interp.shape[0]-1:
        data_res[p] = data_res[p] + beta2 * data_interp[p_punkt+2]
time_elapsed_s = (time.time() - time_start)/sigLen_s
# endregion

# region... 4. Evaluate execution time and resampling quality in terms of SINR values
cut = 150
data_eval = data_norm[(0+cut):(data_norm.shape[0]-cut), :]
data_eval_res = data_res[(0+cut):(data_res.shape[0]-cut), :]

power_ref_sig = np.mean(data_eval[:, 0]**2)

interp_noise = data_eval[:, 0]-data_eval[:, 1]
power_interp_noise = np.mean(interp_noise**2)
sinr_in_dB = 10*np.log10(power_ref_sig/power_interp_noise)

interp_noise = data_eval[:, 0]-data_eval_res[:, 0]
power_interp_noise = np.mean(interp_noise**2)
sinr_res_dB = 10*np.log10(power_ref_sig/power_interp_noise)

#print('Input-SNR=' + str(sinr_in_dB) + 'dB and Output-SNR=' + str(sinr_res_dB) + 'dB')
print('... execution time per second of input data: %4.2f sec' % time_elapsed_s)
print('... signal-to-interpolation-noise ratio (SINR): input=%4.2f dB, output=%4.2f dB' % (sinr_in_dB, sinr_res_dB))

#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_eval[:, 0], label='Mic-1')
#ax1.plot(data_eval[:, 1], label='Mic-2')
#ax1.plot(data_eval_res[:,0], linestyle=':', label='Res')
#plt.legend(); plt.show()

#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_eval[:, 0]-data_eval_res[:,0], linestyle=':', label='(Mic-1)-(Res)')
#plt.legend(); plt.show()
# endregion
