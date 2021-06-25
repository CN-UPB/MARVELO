import os
import numpy as np
from time import time


class PipeReader:
    def __init__(self, fd, block_shape, initial_clear=False,
                 blocking_read_threshold=1, dtype=np.float32):
        """
        Reads data blocks from the pipe

        The option initial clear can be used to discard the data blocks, that
        are  already in the pipe, when the reader is started. This can be used
        to compensate the effect that spark is already writing to the pipe
        while the python script is starting.

        Args:
            :param fd: file descriptor of the pipe to be read
            :param block_shape: shape to which the read blocks are converted
            :param initial_clear: if True the pipe is cleared,
                                  when the reader is started
            :param blocking_read_threshold: threshold indicating the time point
                                            at which the pipe is cleared
            :param dtype: dtype of the data to be read
        """
        self.fd = fd
        self.block_shape = block_shape
        self.dtype = dtype
        self.bytes_per_block = np.prod(block_shape) * dtype().nbytes
        self.buffer = list()
        self.byte_count = 0
        self.blocking_read_treshold = blocking_read_threshold

        if initial_clear:
            start_read = time()
            while time() - start_read < self.blocking_read_treshold:
                start_read = time()
                self.read_block(discard_block=True)


    def read_block(self, discard_block=False):
        """
        Reads one block of data from the pipe

        Args:
            param discard_block: if True the read block will be discarded and
                                 not returned

        Return:
             A numpy array containing the data of the read block
        """
        # read single bytes from the pipe and write the to the buffer
        # until a full block is read
        while self.byte_count < self.bytes_per_block:
            self.buffer.append(os.read(self.fd, self.bytes_per_block))
            self.byte_count += len(self.buffer[-1])

        # seperate the block from the read bytes and write the remaining bytes
        # to the buffer
        bytes = b"".join(self.buffer)
        self.buffer = [bytes[self.bytes_per_block:]]
        self.byte_count = len(self.buffer[-1])

        # convert the byte string to a numpy array if the block should
        # not be discarded
        if not discard_block:
            x = np.fromstring(
                bytes[:self.bytes_per_block], dtype=self.dtype
            ).reshape(self.block_shape)
            return x
