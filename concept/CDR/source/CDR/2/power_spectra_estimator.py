#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-11-27

import numpy as np
import sys

class PowerSpectraEstimator(object):
    def __init__(self, frame_len, fft_len, smoothing_factor, min_bin, max_bin,
                 num_channels):
        self._frame_length = frame_len
        self._fft_length = fft_len
        self._smoothing_factor = smoothing_factor
        self._number_of_channels = num_channels
        self._minimum_fft_bin = min_bin
        self._maximum_fft_bin = max_bin
        self._window = np.hanning(self._frame_length).reshape((-1, 1))
        self._power_spectra = np.zeros((max_bin - min_bin + 1,
                                        num_channels * (num_channels + 1) / 2),
                                       dtype=np.complex)
        self._power_spectra_update = np.empty(self._power_spectra.shape,
                                              dtype=np.complex)

    def process(self, current_frame):
        frame_len, num_channels = current_frame.shape
        if frame_len != self._frame_length:
            raise ValueError("Expected frame of length {}, got {}"
                             .format(self._frame_length, frame_len))
        
        for i in range(frame_len):
            for j in range(num_channels):
                if(current_frame[i,j] != current_frame[i,j]):
                    print("NaN detected at: " + str(i) + ", " + str(j))
                    sys.stdout.flush()

        frame_fd = np.fft.fft(current_frame * self._window, self._fft_length,
                              axis=0)
        frame_fd = frame_fd[self._minimum_fft_bin:(self._maximum_fft_bin + 1),
                            :]
        smoothing_factor = self._smoothing_factor
        if np.array_equal(self._power_spectra,
                          np.zeros(self._power_spectra.shape)):
            smoothing_factor = 0.0
        self._power_spectra *= smoothing_factor
        update_idx = 0
        for chan1 in range(self._number_of_channels):
            for chan2 in range(chan1, self._number_of_channels):
                self._power_spectra_update[:, update_idx] = \
                        frame_fd[:, chan1] * np.conjugate(frame_fd[:, chan2])
                update_idx += 1
        self._power_spectra += (1 - smoothing_factor) * \
                self._power_spectra_update
        return self._power_spectra


if __name__ == "__main__":
    raise NotImplementedError()
