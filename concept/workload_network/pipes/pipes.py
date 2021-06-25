from fission.core.pipes import BasePipe

class FloatPipe(BasePipe):
    BLOCK_SIZE = 4

    def pack(self, data):
        import struct
        data = struct.pack("!f", data)
        return data

    def unpack(self, data):
        import struct
        data = struct.unpack("!f", data)[0]
        return data