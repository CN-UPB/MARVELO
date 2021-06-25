import array
import logging
import pickle
import queue
import struct
import threading
import json
from pickletools import (TAKEN_FROM_ARGUMENT1, TAKEN_FROM_ARGUMENT4,
                         TAKEN_FROM_ARGUMENT4U, TAKEN_FROM_ARGUMENT8U,
                         UP_TO_NEWLINE, code2op)

from fission.core.base import BasePipe

logger = logging.getLogger(__name__)

# ─── GENERAL MIXINS ─────────────────────────────────────────────────────────────


class OptionalMixIn():
    ASYNC = True

    OPTIONAL_DEFAULT = None
    OPTIONAL_STORE = True
    OPTIONAL_BUFFER_SIZE = 0
    OPTIONAL_DELETE_MODE = 'oldest'

    def __init__(self, *args, **kwargs):
        """This MixIn creates a pipe which does not have to read data for each time `run` is called.  
        Instead you can define a default value which should be returned by the pipe's `read` method.
        If the pipe received a value, this will be returned instead.  
        You may also set whether the value should be saved, and replace the default value or just should be passed once and afterwards fall back on the old default value if no new inputs are available.  
        At last you can also set a buffer size indicating how many inputs the pipe is allowed to buffer before deleting data.

        This MixIn enables the `ASYNC` flag.

        This behaviour is achieved by calling `super().read()` in a thread while overriding the `read` method and having a queue between main and sub thread.
        This means this MixIn can only be used to **extend a existing pipe** by having the `OptionalMixIn` before the pipe you wish to extend in the mro.

        ```python
        class MyOptionalPipe(OptionalMixIn, MyNormalPipe):
            OPTIONAL_DEFAULT = "And now I override the class attributes"
        ```
        """
        super().__init__(*args, **kwargs)

        self._default = self.OPTIONAL_DEFAULT
        self._store = self.OPTIONAL_STORE

        self._optional_mix_in_buffer_size = self.OPTIONAL_BUFFER_SIZE
        self._optional_mix_in_thread = None
        self._optional_mix_in_queue = None
        if self.OPTIONAL_DELETE_MODE in ['newest', 'oldest']:
            self._optional_mix_in_delte_mode = self.OPTIONAL_DELETE_MODE
        else:
            raise RuntimeError(
                f"OPTIONAL_DELETE_MODE of {self} must be 'newest' or 'oldest'")

        if self._store:
            self._recent_value = self._default

    def _read(self, file_obj):
        while True:
            value = super().read(file_obj)
            try:
                self._optional_mix_in_queue.put_nowait(value)
            except queue.Full:
                if self._optional_mix_in_delte_mode == "oldest":
                    try:
                        self._optional_mix_in_queue.get_nowait()
                        self._optional_mix_in_queue.put(value)
                    except queue.Empty:
                        self._optional_mix_in_queue.put(value)

    def read(self, file_obj):
        if self._optional_mix_in_thread != None:
            try:
                value = self._optional_mix_in_queue.get_nowait()
                self._recent_value = value
            except queue.Empty:
                if self._store:
                    value = self._recent_value
                else:
                    value = self._default
            return value
        else:
            self._optional_mix_in_thread = threading.Thread(
                target=self._read, args=(file_obj,), daemon=True)
            self._optional_mix_in_queue = queue.Queue(
                self._optional_mix_in_buffer_size)
            self._optional_mix_in_thread.start()
            return self.read(file_obj)


# ─── PICKLE ─────────────────────────────────────────────────────────────────────

class ReadPickleMixIn:
    def read(self, file_obj):
        data = pickle.load(file_obj)
        return data

    def read_wrapper(self, file_obj):
        """Reads pickle data without loading it.

        Arguments:
            file_obj {file like} -- File object to read from

        Raises:
            EOFError: When EOF is reached
        """
        buffer = b''
        while True:
            code = file_obj.read(1)
            if not code:
                raise EOFError
            buffer += code
            code = code.decode("latin-1")
            opcode = code2op[code]
            if opcode.arg is not None:
                n = opcode.arg.n
                if n > 0:
                    buffer += file_obj.read(n)
                elif n == UP_TO_NEWLINE:
                    if code in ['i', 'c']:
                        n = 2
                    else:
                        n = 1
                    for i in range(n):
                        buffer += file_obj.readline()

                elif n == TAKEN_FROM_ARGUMENT1:
                    n = file_obj.read(1)
                    buffer += n
                    n = ord(n)
                    buffer += file_obj.read(n)
                elif n == TAKEN_FROM_ARGUMENT4:
                    n = file_obj.read(4)
                    buffer += n
                    n, = struct.unpack("<i", n)
                    buffer += file_obj.read(n)
                elif n == TAKEN_FROM_ARGUMENT4U:
                    n = file_obj.read(4)
                    buffer += n
                    n, = struct.unpack("<I", n)
                    buffer += file_obj.read(n)
                elif n == TAKEN_FROM_ARGUMENT8U:
                    n = file_obj.read(8)
                    buffer += n
                    n, = struct.unpack("<Q", n)
                    buffer += file_obj.read(n)
            if code == '.':
                break
        return buffer


class WritePickleMixIn:
    def write(self, file_obj, data):
        # print(f"Writing {data} @ {self} {file_obj}")
        while True:
            try:
                pickle.dump(data, file_obj)
                break
            except BrokenPipeError:
                pass


class PickleMixIn(ReadPickleMixIn, WritePickleMixIn):
    """This MixIn does not require overriding pack and unpack
    as pickle already functions with Python objects.
    """
    pass


class PicklePipe(PickleMixIn, BasePipe):
    BLOCK_SIZE = "PKL"


class OptionalPicklePipe(OptionalMixIn, PicklePipe):
    pass

# ─── JSON ───────────────────────────────────────────────────────────────────────


class ReadJSONMixIn():
    """This MixIn Reads JSON from the pipe and converts it.
    It expects the JSON to be send in one line and finished with a linebreak.
    Encoding should be UTF8.
    """

    def read_wrapper(self, file_obj):
        return file_obj.readline()

    def read(self, file_obj):
        return file_obj.readline()

    def unpack(self, data):
        return json.loads(data.decode("utf-8"))


class WriteJSONMixIn():
    """This MixIn Writes JSON to the pipe. It is written in one line and ends 
    with a linebreak. It is encoded in UTF8.
    """

    def write(self, file_obj, data):
        file_obj.write(data)

    def pack(self, data):
        _data = json.dumps(data) + "\n"
        return _data.encode("utf-8")


class JSONMixIn(ReadJSONMixIn, WriteJSONMixIn):
    """Combines ReadJSONMixIn and WriteJSONMixIn.
    """
    pass


class JSONPipe(JSONMixIn, BasePipe):
    """Combines JSONMixIn with BasePipe.
    Can be used as a Pipe without further action.
    """
    BLOCK_SIZE = "JSON"


class OptionalJSONPipe(OptionalMixIn, JSONPipe):
    """Combines OptionalMixIn and JSONPipe.
    """
    pass

# ─── OTHER PIPES ────────────────────────────────────────────────────────────────


class BytesPipe(BasePipe):
    def __init__(self, id, block_size, block_count=1):
        """A Pipe which only asks for number of bytes and optionally 
        a block count. Useful for connecting ExecutableJobs which take
        no advantage of pack-/unpack-methods.

        Arguments:
            id {int} -- Unique pipe id
            block_size {int} -- Number of bytes sent per block

        Keyword Arguments:
            block_count {int} -- Number of blocks expected at receiving end (default: {1})
        """
        super().__init__(id)
        if not isinstance(block_size, int) or block_size < 1:
            raise ValueError("Block size must be integer >= 1.")
        if not isinstance(block_count, int) or block_count < 1:
            raise ValueError("Block count must be integer >= 1.")

        self.BLOCK_SIZE = block_size
        self.BLOCK_COUNT = block_count


class OptionalBytesPipe(OptionalMixIn, BytesPipe):
    pass


# ─── INTERNAL USE ───────────────────────────────────────────────────────────────


class LoaderPipe(BasePipe):
    """A Pipe specific for loader module.
    Adds validation by changing BLOCK_SIZE and BLOCK_COUNT to properties.
    This class bypasses some sanity checking and is not meant for use outside a Loader.
    """
    BLOCK_SIZE = None
    BLOCK_COUNT = None

    @property
    def block_size(self):
        return self.BLOCK_SIZE

    @block_size.setter
    def block_size(self, value):
        if not isinstance(value, int) and value > 0:
            raise RuntimeError(
                f"Pipe {self.id}: Block size needs to be integer >= 1.")
        if not self.block_size:
            self.BLOCK_SIZE = value
        elif self.block_size and (self.block_size != value):
            raise RuntimeError(
                f"Multiple block sizes are set for pipe {self.id}.")

    @property
    def block_count(self):
        return self.BLOCK_COUNT

    @block_count.setter
    def block_count(self, value):
        if not isinstance(value, int) and value > 0:
            raise RuntimeError(
                f"Pipe {self.id}: Block count needs to be integer >= 1.")
        if not self.block_count:
            self.BLOCK_COUNT = value
        elif self.block_count and (self.block_count != value):
            raise RuntimeError(
                f"Multiple block counts are set for pipe {self.id}.")
