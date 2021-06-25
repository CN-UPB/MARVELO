from fission.core.pipes import PicklePipe, OptionalPicklePipe

class OperatorPipe(OptionalPicklePipe):
    OPTIONAL_DEFAULT = "+"
    OPTIONAL_STORE = True
    OPTIONAL_BUFFER_SIZE = 1
    OPTIONAL_DELETE_MODE = 'oldest'

class ReducePipe(PicklePipe):
    BLOCK_COUNT = 5