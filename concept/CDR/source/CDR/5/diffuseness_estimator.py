#!/usr/bin/env python
#
# Author: Markus Bachmann, LMS, FAU
# Date: 2017-11-27
#
# References:
#   [1] Giovanni Del Galdo, Maja Taseska, Oliver Thiergart, Jukka Ahonen,
#       and Ville Pulkki, "The diffuse sound field in energetic analysis," The
#       Journal of the Acoustic Society of America, vol. 131, no. 3, pp.
#       2141-2151, 2012
#   [2] Andreas Schwarz and Walter Kellermann, "Coherent-to-Diffuse Power Ratio
#       Estimation for Dereverberation," IEEE/ACM Transactions on Audio,
#       Speech, and Language Processing, vol. 23, pp. 1006-1018, June 2015

import numpy as np

class DiffusenessEstimator(object):
    def __init__(self, diffuseness_buffer_size, num_channel_combinations):
        self._next_diffuseness_buffer_index = 0
        self._diffuseness_buffer = np.zeros((diffuseness_buffer_size,
                                             num_channel_combinations),
                                            dtype=float)

    def process(self, cdr):
        diffuseness = 1.0 / (cdr + 1.0)
        self._diffuseness_buffer[self._next_diffuseness_buffer_index, :] = \
                np.mean(diffuseness, axis=0)
        self._next_diffuseness_buffer_index = \
                (self._next_diffuseness_buffer_index + 1) % \
                self._diffuseness_buffer.shape[0]
        averaged_diffuseness = np.mean(self._diffuseness_buffer, axis=0)
        assert np.all(0. <= averaged_diffuseness) and \
                np.all(averaged_diffuseness <= 1.)
        return averaged_diffuseness


if __name__ == "__main__":
    raise NotImplementedError()
