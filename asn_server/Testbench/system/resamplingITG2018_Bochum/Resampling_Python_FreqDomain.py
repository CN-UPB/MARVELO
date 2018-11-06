import scipy.io.wavfile
import time
from Resampling_Python_FreqDomain_functions import *


# 1. Read data for resampling for a given SRO value
dftLen_N = 2**9  # fft length (8 or 9)

sro = 100  # sampling rate offset in ppm
fs, x_k = scipy.io.wavfile.read(
    'AudioData/Exp_1_FS_50_FE_6500_Length_30_BaseFreq_16000_SRO_' + str(sro) + '.wav')  # read audio signals from file
print('**************',fs)

sigLen_sec = 10  # length of input signal

data_transp = np.transpose(x_k[0:sigLen_sec * fs, :])  # transpose input signal to get row vector
data_norm = data_transp / np.max(np.hstack((data_transp[0, :], data_transp[1, :])))  # normalize input signal

lenLowRateFir_Np = 100  # length of convolved FIR filter g_sc on low rate
parConvFD_L_max = 8  # upsampling factor

parConv_interpType = 'Lagrange'
parConv_Na = 4

print('\nSampling rate offset (SRO): %4.2fppm' % sro)

# 2. Calculate necessary filters with appropriate parameters and initialize resampler
f_p_lowpass_Hz = 7000
f_s_lowpass_Hz = int(fs/2)
f_ps_lowpass_Hz = [f_p_lowpass_Hz, f_s_lowpass_Hz]

parConvFD_L = np.min(np.hstack((np.floor(1/(sro*1e-6*(dftLen_N-lenLowRateFir_Np+1))), parConvFD_L_max)))
if parConvFD_L < 2:
    print('ERROR: Upsampling factor L is too small: set smaller value of FFT length!')

_, g_sc_fft, _, _ = initmonolithicfarrow(
    parConvFD_L, lenLowRateFir_Np, f_ps_lowpass_Hz, parConv_interpType, parConv_Na, dftLen_N, fs)

# 3. Perform resampling
print('Perform resampling by using PolyFar-FFT method...')

time_start = time.time()
data_res, n_firstLast = resamplingmonolithicfarrow_fd(
    data_norm[1, :], sro, parConvFD_L, lenLowRateFir_Np, parConv_interpType, g_sc_fft, dftLen_N)
proc_time_per_sec = (time.time() - time_start)/sigLen_sec

# 4. Evaluate execution time and resampling quality in terms of SINR values
cut = np.int(dftLen_N*1.5)
data_eval = data_norm[:, (0 + cut):(data_norm.shape[1] - cut)]
data_eval_res = data_res[:, (0+cut):(data_res.size-cut)]

power_ref_sig = np.mean(data_eval[0, :]**2)

interp_noise = data_eval[0, :]-data_eval[1, :]
power_interp_noise = np.mean(interp_noise**2)
sinr_in_dB = 10*np.log10(power_ref_sig/power_interp_noise)

interp_noise = data_eval[0, :]-data_eval_res
power_interp_noise = np.mean(interp_noise**2)
sinr_out_dB = 10*np.log10(power_ref_sig/power_interp_noise)

# Print resampling results
print('... execution time per second of input data: %4.2f sec' % proc_time_per_sec)
print('... signal-to-interpolation-noise ratio (SINR): input=%4.2f dB, output=%4.2f dB' % (sinr_in_dB, sinr_out_dB))

# print('\nSampling rate offset (SRO): %4.2fppm' % sro)
# print('SINR: input=%4.2fdB, output=%4.2fdB' % (sinr_in_dB, sinr_out_dB))
# print('Processing time per second of input data: %4.3fs' % proc_time_per_sec)
