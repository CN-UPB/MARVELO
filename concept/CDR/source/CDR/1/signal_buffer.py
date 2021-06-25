# Author: Markus Bachmann, LMS, FAU
# Date: 2018-06-19

import numpy as np

class SignalBuffer(object):
    def __init__(self, frame_length, number_channels):
        self._signal_buffer = np.zeros(frame_length * number_channels)


    def process(self, innovation):
        innovation_length = len(innovation)
        self._signal_buffer[:-innovation_length] = \
                self._signal_buffer[innovation_length:]
        self._signal_buffer[-innovation_length:] = innovation
        return self._signal_buffer
