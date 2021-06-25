from fission.core.pipes import OptionalPicklePipe

class InteractivePipe(OptionalPicklePipe):
    OPTIONAL_DEFAULT = 20
    OPTIONAL_BUFFER_SIZE = 1

    def pack(self, value):
        try:
            result = int(value.strip())
        except ValueError:
            result = 0
        return result