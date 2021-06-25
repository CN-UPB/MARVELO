#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-12-27
#
# References:
#   [1] Andreas Schwarz and Walter Kellermann, "Coherent-to-Diffuse Power Ratio
#       Estimation for Dereverberation," IEEE/ACM Transactions on Audio,
#       Speech, and Language Processing, vol. 23, pp. 1006-1018, June 2015

import numpy as np

class CDREstimator(object):
    def __init__(self, fft_length, num_channels, channel_combinations,
                 sampling_frequency, speed_of_sound, sensor_positions, min_bin,
                 max_bin):
        if max(max([list(cc) for cc in channel_combinations])) > num_channels:
            raise ValueError("inconsistent given number of channels and "
                             "channel combinations")

        noise_coherence = np.empty((fft_length, len(channel_combinations)),
                                   dtype=np.float)
        frequencies = np.linspace(0, sampling_frequency, fft_length)
        tmp = 2.0 * frequencies / speed_of_sound
        idx = 0
        for chan1 in range(num_channels):
            for chan2 in range(chan1 + 1, num_channels):
                if not (chan1, chan2) in channel_combinations:
                    continue
                d = np.linalg.norm(sensor_positions[chan1, :] -
                                   sensor_positions[chan2, :])
                noise_coherence[:, idx] = np.sinc(tmp * d)
                idx += 1
        self._noise_coherence = noise_coherence[min_bin:(max_bin + 1), :]
        assert np.all(0. <= np.abs(self._noise_coherence)**2.) and \
                np.all(np.abs(self._noise_coherence)**2. <= 1.)

    def process(self, signal_coherence):
        magnitude_threshold = 1.0 - 1e-10
        critical = np.abs(signal_coherence) > magnitude_threshold
        signal_coherence[critical] = magnitude_threshold * \
                signal_coherence[critical] / np.abs(signal_coherence[critical])
        tmp = self._noise_coherence * np.real(signal_coherence)
        cdr = (tmp - np.abs(signal_coherence)**2.0 -
               np.sqrt(tmp**2.0 - (self._noise_coherence *
                                   np.abs(signal_coherence))**2.0 +
                       self._noise_coherence**2.0 - 2.0 * tmp +
                       np.abs(signal_coherence)**2.0)) / \
              (np.abs(signal_coherence)**2.0 - 1.0)
        return np.maximum(cdr.real, 0.)


if __name__ == "__main__":
    raise NotImplementedError()
