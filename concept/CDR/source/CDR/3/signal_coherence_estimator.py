#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-11-27

import numpy as np
import sys

class SignalCoherenceEstimator(object):
    def __init__(self, num_channels, channel_combinations, min_bin, max_bin):
        self._number_of_channels = num_channels
        self._channel_combinations = channel_combinations
        self._coherence = np.empty((max_bin - min_bin + 1,
                                    len(channel_combinations)),
                                   dtype=np.complex)
        self._auto_power_spectra_indices = list()

        # Create auto power spectra lookup-table
        stepsize = num_channels
        idx = 0
        while stepsize > 0:
            self._auto_power_spectra_indices.append(idx)
            idx += stepsize
            stepsize -= 1


    def process(self, power_spectra):
        idx = 0
        out_idx = 0
        for chan1 in range(self._number_of_channels):
            idx += 1
            for chan2 in range(chan1 + 1, self._number_of_channels):
                idx += 1
                if not (chan1, chan2) in self._channel_combinations:
                    continue
                self._coherence[:, out_idx] = power_spectra[:, idx - 1] / \
                        (np.sqrt(
                                power_spectra[:,
                                    self._auto_power_spectra_indices[chan1]] * \
                                power_spectra[:,
                                    self._auto_power_spectra_indices[chan2]]
                                ) + np.finfo(power_spectra.dtype).eps)
                out_idx += 1
        assert np.all(0. <= np.abs(self._coherence)**2.)
        assert np.all(np.abs(self._coherence)**2. <= 1. + 1e-8)
        return self._coherence


if __name__ == "__main__":
    raise NotImplementedError()
