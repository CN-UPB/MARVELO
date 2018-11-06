import numpy as np
# from scipy import signal
from scipy import io


def initmonolithicfarrow(
        upsampfactor_l, len_low_rate_fir_n, lowpass_freqs, interpol_type, len_async_interp_na, dft_len, fs):
    """In this function, FIR-filters are calculated (or loaded) for a sub-herz precision using a monolithic low-rate
    Farrow structure comprising a fixed upsampler (L=4) followed by a causal lowpass FIR filter and a quasi-continuously
    interpolation (e.g. Lagrange or Farrow filter) [1].

    [1] 'Low-Rate Farrow Structure with Discrete-Lowpass and Polynomial Support for Audio Resampling' from A. Chinaev &
    P. Thuene & G. Enzner submitted to Eusipco-2018

    upsampFactor_L -- upsampling factor (scalar)
    lenLowRateFir_N -- length of convolved FIR filter g_sc on low rate (scalar)
    lowpassFreqs -- lowpass frequencies in Hz [fd fs] (list)
    interpolType -- type of used interpolation (string)
    lenAsyncInterp_Na -- branch length of asynch. interpolator (scalar)
    dftLen_N -- dft length (scalar)
    fs -- sampling frequency (scalar)
    """

    # validity check of input parameters
    r = 4
    upsampfactor = int(upsampfactor_l)

    if np.array(lowpass_freqs).size < 2 or np.min(lowpass_freqs) < 0 or lowpass_freqs[0] > lowpass_freqs[1]:
        print('Parameter lowpassFreqs is not valid!!!')
    if len_low_rate_fir_n < 2:
        print('Set appropriate parameter lenLowRateFir_N > =1 !!!')
    if interpol_type != 'Lagrange':
        print('Set parameter interpolType to Lagrange')
    if interpol_type == 'Lagrange' and len_async_interp_na != 4:
        print('Inappropriate parameter lenAsyncInterp_Na. For Lagrange interpolator set lenAsyncInterp_Na=4!!!')

    # design of high-rate lowpass filter g_s (for synchronous interpolation)
    len_g_sc_high_rate = upsampfactor * len_low_rate_fir_n  # length of convolved filter on high rate
    len_lowpass_hi_rate = len_g_sc_high_rate - len_async_interp_na + 1  # length of lowpass filter on high rate

    mat = io.loadmat('MatFiles/firpm_B797.mat')
    g_s = upsampfactor * np.transpose(mat['B'])

    # design of high-rate asynchronous (continuous) interpolation filter g_c
    filtcoeff = np.array([[0, -1/6, 0, 1/6], [0, 1, 1/2, -1/2], [1, -1/2, -1, 1/2], [0, -1/3, 1/2, -1/6]])

    idx = list(range(0, filtcoeff.shape[0]))
    idx.reverse()
    g_c_all = filtcoeff[idx, :]

    # fuse a lowpass filter with an asynchronous interpolation filter to g_sc
    g_sc = np.zeros((r, len_g_sc_high_rate))
    for order in range(0, r):
        g_sc[order, :] = np.convolve(g_s[:, 0], filtcoeff[:, order])

    g_sc_fft = np.zeros((r, int(upsampfactor * dft_len)), dtype=complex)
    for ell in range(0, upsampfactor):
        a = list(range(0, g_sc_fft.shape[1], upsampfactor))
        b = [x+ell for x in a]
        c = list(range(0, g_sc.shape[1], upsampfactor))
        d = [x+ell for x in c]
        g_sc_fft[:, b] = np.fft.fft(g_sc[:, d], dft_len)

    return g_sc, g_sc_fft, g_s, g_c_all


def resamplingmonolithicfarrow_fd(x_k, sro_ppm, upsamp_factor, len_g_sc_low_rate, interpol_type, g_sc_fft, dft_len):
    """Resample data in frequency domain with sub-herz precision using a monolithic low-rate Farrow structure comprising
    a fixed upsampler (L=4) followed by a causal lowpass FIR-filter and a quasi-continuously interpolation (e.g.
    Lagrange or Farrow filter) [1].
    [1] 'Low-Rate Farrow Structure with Discrete-Lowpass and Polynomial Support for Audio Resampling' from A. Chinaev
    & P. Thuene & G. Enzner submitted to Eusipco-2018.

    Caution!!! Implemented only for positive sro_ppm values (sro_ppm > 0)

    Keyword arguments:
    x_k -- signal (vector)
    sro_ppm -- sampling-rate offset in ppm (scalar > 0)
    upsampFactor_L -- upsampling factor (scalar)
    len_g_sc_low_rate -- length of FIR on low rate f_y (scalar)
    interpolType -- type of used interpolation (string)
    g_sc_fft -- fft of monolithic FIR (R x (L*dftLen_N) matrix)
    dftLen_N -- dft length (scalar)

    y_n -- resampled signal (vector)
    n_firstLast -- first and last valid output time points to avoid settling/transient period if necessary (vector)
    """

    # validity check of input parameters
    pol_order = 4  # polynomial order
    interp_factor = upsamp_factor  # interpolation factor L

    if len_g_sc_low_rate < 2:
        print('Set appropriate parameter len_g_sc_low_rate > =1 !!!')

    len_g_sc_low_rate_half = int(len_g_sc_low_rate/2)

    if len_g_sc_low_rate_half % 1 != 0:
        print('The variable len_g_sc_low_rate_half has to be an integer')

    if interpol_type != 'Lagrange':
        print('Set parameter interpolType to Lagrange')

    if g_sc_fft.shape[1] != interp_factor*dft_len:
        print('Inconsistent pars: size(g_sc_fft,2), L and dftLen_N!!!')

    if g_sc_fft.shape[0] != pol_order:
        print('Set appropriate polynomial order R=4')

    # calculate true delays of x(k) for given constant sro for output y(n)
    y_n = np.zeros((1, x_k.size))
    len_sig = y_n.size
    n_vec = np.array(list(range(0, len_sig)))
    delta_n_vec_lowercase = sro_ppm*1e-6*n_vec
    delta_max = delta_n_vec_lowercase[-1]

    # design of high-rate asynchronous (continuous) interpolation filter g_c
    pol_order = g_sc_fft.shape[0]
    delta0 = 0

    # perform a monolithic poly-phase ASRC acc. to Fig. 5 in [1] in 3 steps
    pol_pows = np.array(list(range(0, pol_order)))
    delta_n_vec = np.zeros((1, y_n.size))

    # fft of g_sc
    bl_len_b = dft_len - len_g_sc_low_rate + 1
    idx_lst = bl_len_b - len_g_sc_low_rate_half

    # set first and last valid output time points
    n_first = np.ceil(len_g_sc_low_rate_half)
    n_last = len_sig - 2*bl_len_b - len_g_sc_low_rate_half - np.ceil(delta_max)
    n_first_last = np.array([int(n_first), int(n_last)])

    # perform filtering in the frequency domain (Over-Lap Save)
    w_m_reg_matrix_fft = np.zeros((pol_order, len_sig), dtype=complex)
    w_m_reg_matrix_fft_reg = np.zeros((pol_order, 2*bl_len_b))
    n_bl = list(range(0, bl_len_b))

    mu_n_akt = 0
    nu_n_akt = 0  # time synchronization in the beginning

    idx_chng = None
    nu_change_flag = None

    for idx_bl in range(1, int(np.floor(len_sig/bl_len_b))+1):

        # timings calculated using eq. (3) in [1]
        delta_n_sc = delta_n_vec_lowercase[n_bl]
        mu_n_bl = np.floor(delta_n_sc)  # integer delay
        delta_n_frac = delta_n_sc - mu_n_bl  # {delta_n}
        nu_n_bl = np.floor(interp_factor*delta_n_frac)  # section number {0... L-1}
        delta_n_bl = (interp_factor * delta_n_frac) - nu_n_bl  # fractional delay at high rate [0, 1)
        delta_n_vec[:, n_bl] = delta_n_bl

        # read from the input signal for the following overlap-save
        if dft_len-1 > n_bl[-1]:
            if dft_len - idx_bl*bl_len_b <= 0:
                x_k_vec_akt = x_k[0:idx_bl*bl_len_b]
            else:
                x_k_vec_akt = np.hstack((np.zeros((dft_len - idx_bl * bl_len_b)), x_k[0:idx_bl * bl_len_b]))
        else:
            if n_bl[-1]+mu_n_akt <= len_sig-1:
                a = [x + np.int(mu_n_akt) for x in list(range(n_bl[-1] - dft_len + 1, n_bl[-1] + 1))]
                x_k_vec_akt = x_k[a]
            else:
                n_bl_valid = list(range(n_bl[0]-bl_len_b, len_sig))
                if dft_len-np.array(n_bl_valid).size <= 0:
                    x_k_vec_akt = x_k[n_bl_valid]
                else:
                    x_k_vec_akt = np.hstack((x_k[n_bl_valid], np.zeros(dft_len - np.array(n_bl_valid).size)))

        # filtering in the frequency domain by using overlap-save
        x_k_vec_akt_fft = np.fft.fft(x_k_vec_akt, dft_len)
        a = [l+np.int(nu_n_akt) for l in list(range(0, g_sc_fft.shape[1], int(interp_factor)))]

        w_m_matrix_akt = np.real(np.fft.ifft(g_sc_fft[:, a] * (np.ones((pol_order, 1))*x_k_vec_akt_fft), dft_len))
        w_m_matrix_akt_out = w_m_matrix_akt[:, (len_g_sc_low_rate-1):w_m_matrix_akt.shape[1]]
        w_m_reg_matrix_fft[:, n_bl] = w_m_matrix_akt_out

        # taking into account a delay of FIR filtering
        if idx_bl < np.floor(len_sig/bl_len_b)+1:
            w_m_reg_matrix_fft_reg_b = w_m_matrix_akt_out
        else:
            w_m_reg_matrix_fft_reg_b = np.zeros((pol_order, bl_len_b))

        w_m_reg_matrix_fft_reg = np.hstack(
            (w_m_reg_matrix_fft_reg[:, bl_len_b:w_m_reg_matrix_fft_reg.shape[1]], w_m_reg_matrix_fft_reg_b))
        w_m_reg_matrix_fft_akt = w_m_reg_matrix_fft_reg[:, [np.int((len_g_sc_low_rate/2))+t for t in list(range(0, bl_len_b))]]

        # interval exceeding for Delta [0;1) if necessary (nu_change_flag==1)
        if idx_bl == 1:
            delta_n_vec_pol = np.zeros((1, bl_len_b))
        else:
            del_n_bl_old = delta_n_vec[:, (np.array(n_bl)-bl_len_b).tolist()]
            if nu_change_flag:
                if idx_chng <= bl_len_b-len_g_sc_low_rate_half:
                    if idx_chng == 1:
                        delta_n_vec_pol = np.hstack(
                            ((1+del_n_bl_old[:, idx_chng:idx_lst]), del_n_bl_old[:, idx_lst:del_n_bl_old.shape[1]]))
                    else:
                        h = np.hstack((del_n_bl_old[:, 0:idx_chng], 1+del_n_bl_old[:, idx_chng:idx_lst]))
                        delta_n_vec_pol = np.hstack((h, del_n_bl_old[:, idx_lst:del_n_bl_old.shape[1]]))
                else:
                    h = np.hstack((del_n_bl_old[:, 0:idx_lst], del_n_bl_old[:, idx_lst:idx_chng]-1))
                    delta_n_vec_pol = np.hstack((h, del_n_bl_old[:, idx_chng:del_n_bl_old.shape[1]]))
            else:
                delta_n_vec_pol = del_n_bl_old

        # compensating Delta_n in the time domain
        delta_n_vec_pol = np.power(np.transpose(delta_n_vec_pol * np.ones((4, 1)))+delta0, pol_pows)
        y_n_akt = np.sum(delta_n_vec_pol*np.transpose(w_m_reg_matrix_fft_akt), axis=1)
        y_n[:, n_bl] = y_n_akt

        # check for new value of nu_n_akt (interval exceeding in the next block causes by polyphase changing)
        if np.all(nu_n_bl == nu_n_akt):
            nu_change_flag = 0
        else:
            nu_change_flag = 1
            if np.all(nu_n_bl != nu_n_akt):
                idx_chng = 1
            else:
                a = np.asarray(np.where(nu_n_bl == nu_n_akt))
                for i in a:
                    idx_chng = i[-1]+1

        mu_n_akt = mu_n_bl[-1]
        nu_n_akt = nu_n_bl[-1]

        n_bl = [x+bl_len_b for x in n_bl]
    y_n = np.hstack((y_n[:, bl_len_b:y_n.shape[1]], np.zeros((1, bl_len_b))))
    return y_n, n_first_last
