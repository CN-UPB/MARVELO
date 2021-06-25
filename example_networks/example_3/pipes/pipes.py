from fission.core.pipes import OptionalPicklePipe

class InteractivePipe(OptionalPicklePipe):
    OPTIONAL_DEFAULT = '+'
    OPTIONAL_BUFFER_SIZE = 1

    def pack(self, value):
        try:
            result = str(value.strip())
        except ValueError:
            result = 0
        return result