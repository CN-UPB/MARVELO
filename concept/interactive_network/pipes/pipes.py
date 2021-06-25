from fission.core.pipes import BasePipe
import struct


class StringToIntPipe(BasePipe):
    BLOCK_SIZE=4
    def unpack(self, data):
        i, = struct.unpack("!i", data)
        return i

    def pack(self, data):
        try:
            b = struct.pack("!i", int(data))
        except ValueError:
            b = struct.pack("!i", 0)
        return b