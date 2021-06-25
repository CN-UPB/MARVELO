import os
import numpy as np


class PipeReader:
    def __init__(self, fd, block_shape, dtype=np.float32):
        self.fd = fd
        self.block_shape = block_shape
        self.dtype = dtype
        self.bytes_per_block = np.prod(block_shape) * dtype().nbytes

        self.buffer = list()
        self.byte_count = 0

    def read_block(self):
        while self.byte_count < self.bytes_per_block:
            self.buffer.append(os.read(self.fd, self.bytes_per_block))
            self.byte_count += len(self.buffer[-1])
        bytes = b"".join(self.buffer)
        self.buffer = [bytes[self.bytes_per_block:]]
        self.byte_count = len(self.buffer[-1])
        x = np.fromstring(
            bytes[:self.bytes_per_block], dtype=self.dtype
        ).reshape(self.block_shape)
        # print(x.tobytes() == bytes[:self.bytes_per_block])
        return x

