# region... Implementation of DXCP-PhaT-CL as a MARVELO-Block
import sys
import math
import numpy as np
from scipy import signal
from config.Parameters_DXCPPhaT import *
# endregion

class DXCPPhaT:

    # Constructor
    def __init__(self):
        self.setStateVar_DXCPPhaT()
        print('... instance object for DXCP-PhaT created ...')
        sys.stdout.flush()

    # set state variables of DXCP-PhaT
    def setStateVar_DXCPPhaT(self):
        """ Initialize state variables of DXCP-PhaT. """
        # scalar variables
        # SRO estimate (updated once per signal segment), also output SRO estimate for JS demo
        self.SROppm_est_seg = 0
        # SSO estimate (updated once per signal segment)
        self.SSOsmp_est_seg = 0
        # current SRO estimate
        self.SROppm_est_ell = 0
        # current SSO estimate
        self.SSOsmp_est_ell = 0
        # time offset between channels at the end of the current DXCP frame (for JS)
        self.TimeOffsetEndSeg_est_out = 0
        # vectors and matrices
        # Averaged CSD with Phase Transform
        self.GCSD_PhaT_avg = np.zeros((FFTsize_dxcp, 1), dtype=complex)
        # Container with past GCSD_PhaT_avg values
        self.GCSD_PhaT_avg_Cont = np.zeros((FFTsize_dxcp, Cont_NumFr), dtype=complex)
        # averaged CSD-2
        self.GCSD2_avg = np.zeros((FFTsize_dxcp, 1), dtype=complex)
        # smoothed shifted first CCF
        self.GCCF1_smShftAvg = np.zeros((2 * Upsilon + 1, 1), dtype=float)
        # input buffer of DXCP-PhaT-CL
        self.InputBuffer = np.zeros((FFTsize_dxcp, 2), dtype=float)
        # counters
        # counter for filling of the input buffer before DXCP-PhaT can be executed
        self.ell_execDXCPPhaT = 1
        # counter within signal sections with reset of CL estimator
        self.ell_inSigSec = 1
        # counter of signal sections
        self.ell_sigSec = np.int16(1)
        # counter of recursive simple averaging over CCF-2
        self.ell_GCCF2avg = 1
        # counter of recursive simple averaging over shifted CCF-1 (used for SSO estimation)
        self.ell_shftCCF1avg = 1

    # process data of the current signal frame
    def process_data(self, x_12_ell):

        # fill the internal buffer of DXCP-PhaT-CL (from right to left)
        self.InputBuffer[np.arange(FFTsize_dxcp - FrameSize_input), :] = \
            self.InputBuffer[np.arange(FrameSize_input, FFTsize_dxcp), :]
        self.InputBuffer[np.arange(FFTsize_dxcp - FrameSize_input, FFTsize_dxcp), :] = x_12_ell

        # execute DXCP-PhaT-CL only if ell_execDXCPPhaT == 16 (for FFTshift_dxcp = 2^11 and FrameSize_input = 2^7)
        if self.ell_execDXCPPhaT == int(FFTshift_dxcp / FrameSize_input):
            # reset counter for filling of the input buffer before DXCP-PhaT can be executed
            self.ell_execDXCPPhaT = 0

            # state update of DXCP-PhaT-CL estimator
            self.dxcpphat_stateupdate()

        # update counter for filling of the input buffer before DXCP-PhaT can be executed
        self.ell_execDXCPPhaT += 1

        # calculate output of DXCP-PhaT estimator (JS demo)
        OutputDXCPPhaTcl = {}
        OutputDXCPPhaTcl['SROppm_est_out'] = self.SROppm_est_seg
        OutputDXCPPhaTcl['TimeOffsetEndSeg_est_out'] = self.TimeOffsetEndSeg_est_out

        return OutputDXCPPhaTcl

    # update state variables of DXCP-PhaT
    def dxcpphat_stateupdate(self):
        # 0) reset counter ell_inSigSec for every new signal section
        if self.ell_inSigSec == ResetPeriod_NumFr + 1:
            self.ell_sigSec += 1
            self.ell_inSigSec = 1
            self.ell_GCCF2avg = 1
            self.ell_shftCCF1avg = 1

        # 1) Windowing to the current frames acc. to eq. (5) in [1]
        analWin = signal.blackman(FFTsize_dxcp, sym=False)
        x_12_win = self.InputBuffer * np.vstack((analWin, analWin)).transpose()

        # 2) Calculate generalized (normaized) GCSD with Phase Transform (GCSD-PhaT) and apply recursive averaging
        X_12 = np.fft.fft(x_12_win, FFTsize_dxcp, 0)
        X_12_act = X_12[:, 0] * np.conj(X_12[:, 1])
        X_12_act_abs = abs(X_12_act)
        X_12_act_abs[X_12_act_abs < X_12_abs_min] = X_12_abs_min  # avoid division by 0
        GCSD_PhaT_act = X_12_act / X_12_act_abs
        if self.ell_inSigSec == 1:  # if new signal section begins
            self.GCSD_PhaT_avg = GCSD_PhaT_act
        else:
            self.GCSD_PhaT_avg = \
                SmoConst_CSDPhaT_alpha * self.GCSD_PhaT_avg + (1 - SmoConst_CSDPhaT_alpha) * GCSD_PhaT_act

        # 3) Fill the DXCP-container with Cont_NumFr number of past GCSD_PhaT_avg
        self.GCSD_PhaT_avg_Cont[:, np.arange(Cont_NumFr - 1)] = self.GCSD_PhaT_avg_Cont[:, 1:]
        self.GCSD_PhaT_avg_Cont[:, (Cont_NumFr - 1)] = self.GCSD_PhaT_avg

        # 4) As soon as DXCP-container is filled with resampled data, calculate the second GCSD based
        # on last and first vectors of DXCP-container and perform time averaging
        if self.ell_inSigSec >= Cont_NumFr + (InvShiftFactor_NumFr - 1) + AddContWait_NumFr:
            # Calculate the second GCSD
            GCSD2_act = self.GCSD_PhaT_avg_Cont[:, -1] * np.conj(self.GCSD_PhaT_avg_Cont[:, 0])
            # simple averaging over the whole signal segment in recursive fashion
            self.GCSD2_avg[:, 0] = ((self.ell_GCCF2avg - 1) * self.GCSD2_avg[:,
                                                    0] + GCSD2_act) / self.ell_GCCF2avg  # resets for ell_GCCF2avg=1
            self.ell_GCCF2avg += 1
            # remove components w.o. coherent components
            GCSD2_avg_ifft = self.GCSD2_avg
            # set lower frequency bins (w.o. coherent components) to 0
            GCSD2_avg_ifft[np.arange(LowFreq_InpSig_fl_bin), 0] = 0
            GCSD2_avg_ifft[np.arange(FFTsize_dxcp - LowFreq_InpSig_fl_bin + 1, FFTsize_dxcp), 0] = 0
            # set upper frequency bins (w.o. coherent components) to 0
            GCSD2_avg_ifft[np.arange(FFT_Nyq - NyqDist_fu_bin - 1, FFT_Nyq + NyqDist_fu_bin), 0] = 0
            # Calculate averaged CCF-2 in time domain
            GCCF2_avg_ell_big = np.fft.fftshift(np.real(np.fft.ifft(GCSD2_avg_ifft, n=FFTsize_dxcp, axis=0)))
            idx = np.arange(FFT_Nyq - Lambda - 1, FFT_Nyq + Lambda)
            GCCF2avg_ell = GCCF2_avg_ell_big[idx, 0]

        # 5) Parabolic interpolation (13) with (14) with maximum search as in [1]
        # and calculation of the remaining current SRO estimate sim. to (15) in [1]
        # As soon as GCSD2_avg is smoothed enough in every reseting section
        if self.ell_inSigSec >= Cont_NumFr + (InvShiftFactor_NumFr - 1) + AddContWait_NumFr + SettlingCSD2avg_NumFr:
            idx_max = GCCF2avg_ell.argmax(0)
            if (idx_max == 0) or (idx_max == 2 * Lambda):
                DelATSest_ell_frac = 0
            else:
                # set supporting points for search of real-valued maximum
                sup_pnts = GCCF2avg_ell[np.arange(idx_max - 1, idx_max + 2)]  # supporting points y(x) for x={-1,0,1}
                # calculate fractional of the maximum via x_max=-b/2/a for y(x) = a*x^2 + b*x + c
                DelATSest_ell_frac = \
                    (sup_pnts[2, ] - sup_pnts[0, ]) / 2 / ( 2 * sup_pnts[1, ] - sup_pnts[2, ] - sup_pnts[0, ])
            DelATSest_ell = idx_max - Lambda + DelATSest_ell_frac  # resulting real-valued x_max
            self.SROppm_est_ell = DelATSest_ell / B_smpls * 10 ** 6

        # 6) SSO-estimation after removing of SRO-induced time offset in CCF-1
        if self.ell_inSigSec >= Cont_NumFr + (InvShiftFactor_NumFr - 1) + AddContWait_NumFr + SettlingCSD2avg_NumFr:
            # a) phase shifting of GCSD-1 to remove SRO-induced time offset
            timeOffset_forShift = self.SROppm_est_ell * 10 ** (-6) * FFTshift_dxcp * (self.ell_inSigSec - 1)
            idx = np.arange(FFTsize_dxcp).transpose()
            expTerm = np.power(math.e, 1j * 2 * math.pi / FFTsize_dxcp * timeOffset_forShift * idx)
            GCSD1_smShft = self.GCSD_PhaT_avg * expTerm
            # b) remove components w.o. coherent components
            GCSD1_smShft_ifft = GCSD1_smShft
            # set lower frequency bins (w.o. coherent components) to 0
            GCSD1_smShft_ifft[np.arange(LowFreq_InpSig_fl_bin),] = 0
            GCSD1_smShft_ifft[np.arange(FFTsize_dxcp - LowFreq_InpSig_fl_bin + 1, FFTsize_dxcp),] = 0
            # set upper frequency bins (w.o. coherent components) to 0
            GCSD1_smShft_ifft[np.arange(FFT_Nyq - NyqDist_fu_bin - 1, FFT_Nyq + NyqDist_fu_bin),] = 0
            # c) go into the time domain via calculation of shifted GCC-1
            GCCF1_sroComp_big = np.fft.fftshift(np.real(np.fft.ifft(GCSD1_smShft_ifft, n=FFTsize_dxcp)))
            GCCF1_sroComp = GCCF1_sroComp_big[np.arange(FFT_Nyq - Upsilon - 1, FFT_Nyq + Upsilon),]
            # d) averaging over time and zero-phase filtering within the frame (if necessary)
            self.GCCF1_smShftAvg[:, 0] = \
                ((self.ell_shftCCF1avg - 1) * self.GCCF1_smShftAvg[:, 0] + GCCF1_sroComp) / self.ell_shftCCF1avg
            GCCF1_smShftAvgAbs = np.abs(self.GCCF1_smShftAvg)
            self.ell_shftCCF1avg += 1
            # e) Maximum search over averaged filtered shifted GCC-1 (with real-valued SSO estimates)
            idx_max = GCCF1_smShftAvgAbs.argmax(0)
            if (idx_max == 0) or (idx_max == 2 * Upsilon):
                SSOsmp_est_ell_frac = 0
            else:
                # set supporting points for search of real-valued maximum
                sup_pnts = GCCF1_smShftAvgAbs[
                    np.arange(idx_max - 1, idx_max + 2)]  # supporting points y(x) for x={-1,0,1}
                # calculate fractional of the maximum via x_max=-b/2/a for y(x) = a*x^2 + b*x + c
                SSOsmp_est_ell_frac = \
                    (sup_pnts[2, ] - sup_pnts[0, ]) / 2 / (2 * sup_pnts[1, ] - sup_pnts[2, ] - sup_pnts[0, ])
            self.SSOsmp_est_ell = idx_max - Upsilon + SSOsmp_est_ell_frac  # resulting real-valued x_max

        # 7) Update of SRO and SSO estimates only at the end of signal segment
        if self.ell_inSigSec == ResetPeriod_NumFr:
            # resulting SRO estimate in the first signal section (also output in JS demo)
            self.SROppm_est_seg = self.SROppm_est_ell
            # resulting SSO estimate in the first signal section
            self.SSOsmp_est_seg = self.SSOsmp_est_ell
            # calculate a time offset between channels at the end of the current signal segment (JS demo)
            self.TimeOffsetEndSeg_est_out = \
                self.SSOsmp_est_ell + self.SROppm_est_ell * 10 ** (-6) * FFTshift_dxcp * ResetPeriod_NumFr
            # for new signal segment set SRO and SSO estimates to 0 (steady state for both)
            self.SROppm_est_ell = 0
            self.SSOsmp_est_ell = 0
            # display estimates at the end of the current signal segment
            if Flag_DisplayResults == 1:
                print('%d. Sig-Seg: SRO_ppm=%6.3f; TimeOffset_smp=%6.3f'% (self.ell_sigSec, self.SROppm_est_seg, self.TimeOffsetEndSeg_est_out))
                sys.stdout.flush()

        # update counter of DXCP frames within a signal section until DXCP-PhaT is restarted
        self.ell_inSigSec += 1
