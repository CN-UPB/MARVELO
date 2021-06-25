from fission.core.pipes import BasePipe


class IntPipe(BasePipe):
    BLOCK_SIZE = 4

    def pack(self, data):
        import struct
        data = struct.pack("!I", data)
        return data

    def unpack(self, data):
        import struct
        data = struct.unpack("!I", data)[0]
        return data
