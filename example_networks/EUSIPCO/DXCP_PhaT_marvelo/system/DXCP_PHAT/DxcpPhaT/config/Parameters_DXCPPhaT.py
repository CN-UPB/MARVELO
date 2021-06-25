# region... main parameters of DXCP-PhaT
# reference sampling rate
RefSampRate_fs_Hz = 16000
# frame size (power of 2) of input data
FrameSize_input = 2 ** 11

# frame shift of DXCP-PhaT (power of 2 & >= FrameSize_input)
FFTshift_dxcp = 2 ** 12
# FFT size of DXCP-PhaT (power of 2 & >= FFTshift_dxcp)
FFTsize_dxcp = 2 ** 13

# accumulation time in sec (usually 5s as in DXCP)
AccumTime_B_sec = 5
# (>=2*AccumTime_B_sec) resetting period of DXCP-PhaT in sec
ResetPeriod_sec = 30

# smoothing constant for CSD-PhaT averaging (DXCP-PhaT)
SmoConst_CSDPhaT_alpha = .53
# smoothing constant of SRO-comp. CCF-1 used to estimate d12 (DXCP-PhaT) [.995 for big mic-dist]
# SmoConst_SSOest_alpha = 0

# lower frequency (80 Hz) of input signal in Hz (for ifft)
LowFreq_InpSig_fl_Hz = .01 * RefSampRate_fs_Hz / 2
# upper frequency (7.6 kHz) of input signal in Hz (for ifft)
UppFreq_InpSig_fu_Hz = .95 * RefSampRate_fs_Hz / 2

# additional waiting for container filling (>InvShiftFactor-1)
AddContWait_NumFr = 0
# settling time of CSD-2 averaging (SettlingCSD2avg_NumFr < Cont_NumFr-AddContWait_NumFr)
SettlingCSD2avg_NumFr = 4

# minimum value of |X1*conj(X2)| to avoid devision by 0 in GCC-PhaT
X_12_abs_min = 1e-12
# maximum absolute SRO value possible to estimate (-> Lambda)
SROmax_abs_ppm = 1000

# flag for displaying estimated values in terminal
Flag_DisplayResults = 1
# endregion

# region... help parameters of DXCP-PhaT
# processing rate of DXCP-PhaT
RateDXCPPhaT_Hz = RefSampRate_fs_Hz / FFTshift_dxcp
# number of frames acc. to desired accumulation time B in sec
AccumTime_B_NumFr = int(AccumTime_B_sec // (1 / RateDXCPPhaT_Hz))

# accumulation time B in samples
B_smpls = AccumTime_B_NumFr * FFTshift_dxcp
# maximum lag of the first xcorr
Upsilon = int(FFTsize_dxcp / 2 - 1)
# maximum lag of the second xcorr (DXCP)
Lambda = int(((B_smpls * SROmax_abs_ppm) // 1e6) + 1)

# number of frames in DXCP container
Cont_NumFr = AccumTime_B_NumFr + 1
# number of FFTshift in FFTsize (inverse shift factor)
InvShiftFactor_NumFr = int(FFTsize_dxcp / FFTshift_dxcp)
# number of frames for periodic reset of SRO estimation
ResetPeriod_NumFr = int(ResetPeriod_sec // (1 / RateDXCPPhaT_Hz))

# Nyquist frequency bin
FFT_Nyq = int(FFTsize_dxcp / 2 + 1)
# resolution of frequency axis
FreqResol = RefSampRate_fs_Hz / FFTsize_dxcp
# frequency bin correspondent to LowFreq_InpSig_fl_Hz
LowFreq_InpSig_fl_bin = int(LowFreq_InpSig_fl_Hz // FreqResol)
# frequency bin correspondent to UppFreq_InpSig_fu_Hz
UppFreq_InpSig_fu_bin = int(UppFreq_InpSig_fu_Hz // FreqResol)
# difference FFT_Nyq-UppFreq_InpSig_fu_bin
NyqDist_fu_bin = FFT_Nyq - UppFreq_InpSig_fu_bin
# endregion