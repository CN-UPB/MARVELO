import scipy.io.wavfile
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io

# region... read data (int16 format), normalize them and eliminate an inter-channel starting shift
sro = 10; delay_int_chan = -252; p_del = 1 #   SINR_in =  3.382134 dB, SINR_out = 26.891948 dB
#sro = 40; delay_int_chan = -171; p_del = 1 #  SINR_in = -2.721970 dB, SINR_out = 24.816622 dB
#sro = 50; delay_int_chan = -225; p_del = -1 #  SINR_in = -2.567438 dB, SINR_out = 25.638959 dB
#sro = 80; delay_int_chan = -215; p_del = 0 #  SINR_in = -2.581906 dB, SINR_out = 35.849048 dB
#sro = 100; delay_int_chan = -204; p_del = -1 # SINR_in = -2.237230 dB, SINR_out = 43.947983 dB

rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_' + str(sro) + 'ppm.wav')
#data = data[0:20000]  # cutting data if necessary

data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
data_norm_max = np.max(np.abs(np.hstack((data_norm[:, 0], data_norm[:, 1]))))
data_norm = data_norm.transpose()

data_sync = np.vstack((data_norm[(-delay_int_chan-1):, 0], data_norm[0:(data.shape[0]+delay_int_chan+1), 1]))
data_sync = data_sync.transpose()

#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_sync[:, 0], label='Mic-1'); ax1.plot(data_sync[:, 1], label='Mic-2'); plt.legend(); plt.show()
# endregion

# region... calculate coefficients of a FIR lowpass filter
L=4
filter_fd = 7000
filter_fs = 8000
filter_len = 241
# B = signal.remez(filter_len, [0, filter_fd, filter_fs, rate/2*L], [1, 0], fs=L*rate)
mat = scipy.io.loadmat('MatFiles/firpm_B241.mat'); B_mat = mat['B']; B_mat_tr = B_mat.transpose(); B = B_mat_tr[:,0]

#freq, response = signal.freqz(B)
#plt.plot(0.5*rate*freq/np.pi, 20*np.log10(np.abs(response)), 'b-')
#plt.grid(alpha=0.25); plt.xlabel('Frequency (Hz)'); plt.ylabel('Gain'); plt.show()
# endregion

# region... perform synchronous upsampling with factor L and low-pass filtering
data_new = np.zeros((L*data_sync.shape[0], 1))
data_new[::L, 0] = data_sync[:, 1]

data_new_reshaped = data_new.reshape((data_new.shape[0],))
data_interp = L*signal.lfilter(B, 1.0, data_new_reshaped)

#delay_filt = int((filter_len-1)/2+1)
#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_new_reshaped[0:(data_new_reshaped.shape[0]-delay_filt)], label='data-new')
#ax1.plot(data_interp[delay_filt:], label='interpol')
#plt.legend(); plt.show()
# endregion

# region... perform asynchronous upsampling using Lagrange interpolation
data_resampled = np.zeros((data_sync.shape[0], 1))
for p in range(data_sync.shape[0]):
    delay_akt = 4 * (1+sro*1e-6) * p
    p_punkt = np.int(np.floor(delay_akt))
    nue = delay_akt - p_punkt

    beta_1 = -(nue * (nue - 1) * (nue - 2)) / 6
    beta0 = ((nue + 1) * (nue - 1) * (nue - 2)) / 2
    beta1 = -((nue + 1) * nue * (nue - 2)) / 2
    beta2 = ((nue + 1) * nue * (nue - 1)) / 6

    if p_punkt != 0 and p_punkt <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta_1 * data_interp[p_punkt+p_del-1]
    if p_punkt != 0 and p_punkt+1 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta0 * data_interp[p_punkt+1+p_del-1]
    if p_punkt+2 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta1 * data_interp[p_punkt+2+p_del-1]
    if p_punkt+3 <= data_interp.shape[0]-1:
        data_resampled[p] = data_resampled[p] + beta2 * data_interp[p_punkt+3+p_del-1]
# endregion

# region... evaluate upsampling by using SINR measure
delay_res = int((filter_len-1)/2/L)
data_eval = data_sync[0:(data_sync.shape[0]-delay_res+1), :]
data_resampled_eval = data_resampled[(delay_res-1):, 0]

PowerRef = np.mean(data_eval[:, 0]**2)
InterpolNoise = data_eval[:, 0]-data_eval[:, 1]
PowerNoise = np.mean(InterpolNoise**2); sinr_in_dB = 10*np.log10(PowerRef/PowerNoise)

InterpolNoise = data_eval[:, 0]-data_resampled_eval[:]
PowerNoise = np.mean(InterpolNoise**2); sinr_res_dB = 10*np.log10(PowerRef/PowerNoise)

#fig = plt.figure(figsize=(6, 5)); ax1 = fig.add_subplot(111)
#ax1.plot(data_eval[:, 0], label='Mic-1')
#ax1.plot(data_eval[:, 1], label='Mic-2')
#ax1.plot(data_resampled_eval, label='res-Mic-2')
#plt.legend(); plt.show()

print(sinr_in_dB, sinr_res_dB)
# endregion
