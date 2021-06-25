import logging
import os
import sys
import types
import csv
from inspect import isgeneratorfunction, signature
from pathlib import Path
import subprocess
from functools import reduce
from types import GeneratorType

from fission.core.base import BaseJob


logger = logging.getLogger(__name__)


class PythonJob(BaseJob):

    DEPENDENCIES = None

    def __init__(self, inputs=None, outputs=None):
        """This Job wraps reading and writing to pipes, converting values, 
        redirecting `stdout` and `strerr` and supplies a rustic interface for
        the fission head.

        To create a job just inherit from this class and override the 'run' method.

        Keyword Arguments:
            inputs {list} -- List of input pipes (default: {None})
            outputs {list} -- List of output pipes (default: {None})
        """
        super().__init__(inputs=inputs, outputs=outputs)
        self.finished = False
        self.DEPENDENCIES = self.DEPENDENCIES

    def start(self, root, seperate_job_pipes, redirect_stdout_stderr, **kwargs):
        # logger.debug(
        #     f"{self} started with args: {args}, kwargs: {kwargs} and seperate_job_pipes={seperate_job_pipes}")
        self.setup(root, seperate_job_pipes=seperate_job_pipes, **kwargs)

        in_files, out_files = self.open_pipes(
            root, seperate_job_pipes, **kwargs)

        self.wrapper(in_files, out_files, redirect_stdout_stderr, **kwargs)

    def open_pipes(self, root, seperate_job_pipes=False):
        """Open all pipes for the job placed relativ to 'root'.

        Arguments:
            root {str} -- The root directory for fission

        Keyword Arguments:
            seperate_job_pipes {bool} -- Mostly historical reason, will be True (default: {False})

        Returns:
            tuple -- (<openend in files>, <openend out files>)
        """
        # seperate job pipes needed for sync
        # This only exists due to historical reasons
        if seperate_job_pipes:
            pipe_path = root + "/fifo/{j.id}/{p.id}.fifo"
        else:
            pipe_path = root + "/fifo/{p.id}.fifo"

        in_paths = [pipe_path.format(p=pipe, j=self) for pipe in self.inputs]
        out_paths = [pipe_path.format(p=pipe, j=self) for pipe in self.outputs]

        logger.debug(f"{self}: in pipes: {in_paths}")
        logger.debug(f"{self}: out pipes: {out_paths}")

        in_files = [open(path, "rb") for path in in_paths]
        out_files = [open(path, "wb", 0) for path in out_paths]

        # change cwd to job specific folder
        os.chdir(f"{root}/{self.id}")
        return (in_files, out_files)

    def wrapper(self, in_files, out_files, redirect_stdout_stderr=False):
        """[summary]

        Arguments:
            in_files {list} -- file objects for ingoing pipes (mode = "rb")
            out_files {[type]} -- file objects for outgoing pipes (mode = "wb")

        Keyword Arguments:
            redirect_stdout_stderr {bool/MultiWrite} -- If not False a MultiWrite object is expected. (default: {False})

        Raises:
            RuntimeError: If return value of the 'run' method has a unexpectes shape.
        """

        # check whether run method is generator
        is_gen = self.run() if isgeneratorfunction(self.run) else False

        if redirect_stdout_stderr:
            logger.info(f"Redirecting stdout and stderr for {self}")
            # buffer stdout and stderr
            _stdout = sys.stdout
            _stderr = sys.stderr
            sys.stdout = redirect_stdout_stderr
            sys.stderr = redirect_stdout_stderr

        while True:
            in_data = []
            # read all in pipes
            for i, (in_file, in_pipe) in enumerate(zip(in_files, self.inputs)):
                if in_pipe.BLOCK_COUNT > 1:
                    if self.HEAD:
                        self.in_heads[i] = list()
                    _data = []
                    for _ in range(in_pipe.BLOCK_COUNT):
                        if self.HEAD:
                            self.in_heads[i].append(Head(in_pipe.read_head(in_file), in_pipe._head_size))
                        _data.append(in_pipe.read(in_file))

                    in_data.append([in_pipe.unpack(_d) for _d in _data])
                else:
                    if self.HEAD:
                        self.in_heads[i] = Head(in_pipe.read_head(in_file), in_pipe._head_size)
                    _data = in_pipe.read(in_file)
                    in_data.append(in_pipe.unpack(_data))

            # NOTE meantion in docu!
            if self.inputs and self.HEAD:
                self.head = self.head_reduce()

            if is_gen:
                # get next gen value
                try:
                    out_data = next(is_gen)
                except StopIteration:
                    break
            else:
                # get next value for incoming data
                out_data = self.run(*in_data)

            if out_data == None:
                if out_files:
                    # job has finished
                    break
                else:
                    # job is sink
                    continue

            if not isinstance(out_data, tuple):
                out_data = [out_data] * len(self.outputs)

            if not(len(out_data) == len(out_files)):
                raise RuntimeError("The return value of run() in Job {} has unexpected length: {} instead of {}".format(
                    self.__class__.__name__, len(out_data), len(out_files)))

            for i, (out_file, _data, out_pipe) in enumerate(zip(out_files, out_data, self.outputs)):
                # write to out files
                if self.HEAD:
                    if self.out_heads[i] != None:
                        out_pipe.write_head(out_file, self.out_heads[i])
                        self.out_heads[i] = None
                    elif self.head:
                        out_pipe.write_head(out_file, self.head)
                    else:
                        out_pipe.write_head(out_file, 0)
                # TODO Optimize by calling pack only once for same Pipe types
                _data = out_pipe.pack(_data)
                out_pipe.write(out_file, _data)

            if self.finished:
                break

        # undo stdout/stderr redirection
        if redirect_stdout_stderr:
            sys.stdout = _stdout
            sys.stderr = _stderr

    def finish(self):
        """Has to be called by a source job before finishing to make sure all
        following jobs close properly.
        """
        # TODO variable size
        head_size = 1
        if self.head == None:
            self.head = int("00100000", 2) << (head_size - 1)*8
        else:
            self.head[2] = True
        self.finished = True

    def head_reduce(self):
        """This method describes how the heads from all incoming pipes are
        reduced to a single one.

        By default they are all copared with bitwise or.

        Returns:
            int -- A compressed head
        """
        def compress(L): return reduce(lambda x, y: x | y, L)
        _in_heads = []
        for head in self.in_heads:
            if isinstance(head, list):
                _in_heads.append(compress(head))
            else:
                _in_heads.append(head)
        return compress(_in_heads)


class ExecutableJob(BaseJob):
    DEPENDENCIES = None
    EXECUTABLE = None
    PARAMETERS = None

    INPUT_FLAG = '-i'
    OUTPUT_FLAG = '-o'

    CREATES_SUBPROCESS = True

    def __init__(self, inputs=None, outputs=None):
        """The `ExecutableJob`, as every other job, inherits from [BaseJob](#BaseJob).
        It is for jobs that are not implemented in Python and will execute a given executable in a subprocess.

        The executable need to accept the following arguments:
        - `-i`: The path to a named pipe that should be opened.
          This argument is given as many times there are inputs, 
          they are given in the order they are specified in the config file.

        - `-o`: The path to a named pipe that should be opened.
          This argument is given as many times there are outputs, 
          they are given in the order they are specified in the config file.

        Keyword Arguments:
            inputs {list} -- List of input pipes (default: {None})
            outputs {list} -- List of output pipes (default: {None})
        """
        super().__init__(inputs=inputs, outputs=outputs)

        self.DEPENDENCIES = self.DEPENDENCIES
        self.EXECUTABLE = self.EXECUTABLE
        self.PARAMETERS = self.PARAMETERS
        self.INPUT_FLAG = self.INPUT_FLAG
        self.OUTPUT_FLAG = self.OUTPUT_FLAG

    def start(self, root, seperate_job_pipes=False, redirect_stdout_stderr=False, **kwargs):
        """Make sure ExecutableJob returns subprocess
        """
        # logger.debug(
        #     f"{self} started with args: {args}, kwargs: {kwargs}, seperate_job_pipes={seperate_job_pipes} and redirect={redirect_stdout_stderr}")

        self.setup(root, seperate_job_pipes=seperate_job_pipes,
                   redirect_stdout_stderr=redirect_stdout_stderr, **kwargs)

        command = self.generate_command(root, seperate_job_pipes)

        return self.run(root, command,
                        redirect_stdout_stderr=redirect_stdout_stderr,
                        **kwargs)

    def generate_command(self, root, seperate_job_pipes):
        """Generates the command that should be executed.

        Arguments:
            root {str} -- The root directory of fission
            seperate_job_pipes {bool} -- Historical reaons, will be True

        Returns:
            list -- Command that is executed by Popen
        """
        path = root
        command = self.EXECUTABLE.split()

        if self.PARAMETERS:
            command.extend(self.PARAMETERS.split())

        for pipe in self.inputs:
            if seperate_job_pipes:
                command.extend(
                    [self.INPUT_FLAG, f"{path}/fifo/{self.id}/{pipe.id}.fifo"])
            else:
                command.extend(
                    [self.INPUT_FLAG, f"{path}/fifo/{pipe.id}.fifo"])
        for pipe in self.outputs:
            if seperate_job_pipes:
                command.extend(
                    [self.OUTPUT_FLAG, f"{path}/fifo/{self.id}/{pipe.id}.fifo"])
            else:
                command.extend(
                    [self.OUTPUT_FLAG, f"{path}/fifo/{pipe.id}.fifo"])
        return command

    def run(self, root, command, redirect_stdout_stderr=False):
        """Run generated command in subprocess
        """
        if redirect_stdout_stderr:
            logger.debug(
                f"Redirecting stderr and stdout to {redirect_stdout_stderr}.")
            redirect = redirect_stdout_stderr.writer
        else:
            redirect = subprocess.PIPE
        
        logger.debug(f"{self} executing {command}")
        proc = subprocess.Popen(
            command, cwd=f"{root}/{self.id}", stdout=redirect, stderr=redirect,
            universal_newlines=True, bufsize=1, shell=False)

        return proc

    def __str__(self):
        return "{0.__class__.__name__} {0.id} EXE: {0.EXECUTABLE}".format(self)

    def __repr__(self):
        return f"{self.__class__.__name__} {self.id}"


class DynamicExecutableJob(ExecutableJob):
    def __init__(self, dependencies, executable, parameters='', groups='', input_flag='-i', output_flag='-o', head=False, inputs=None, outputs=None):
        """Same as 'ExecutableJob' but allows to pass dependencies, executable, parameters and groups
        to the __init__. This allows to define a ExecutableJob 
        without the need of setting class attributes.

        Arguments:
            dependencies {str} -- A path to a directory containing all files the executable depends on
            executable {str} -- The actual command for the executable relative to the dependencies directory

        Keyword Arguments:
            parameters {str} -- Any additional parameters (default: {''})
            groups {str} -- Groups of the job (default: {''})
            inputs {list} -- List of input pipes (default: {None})
            outputs {list} -- List of output pipes (default: {None})
        """
        super().__init__(inputs=inputs, outputs=outputs)

        self.DEPENDENCIES = dependencies
        self.EXECUTABLE = executable
        self.PARAMETERS = parameters

        self.HEAD = head

        self.INPUT_FLAG = input_flag
        self.OUTPUT_FLAG = output_flag

        if groups != '':
            self.GROUPS = groups

# ─── MARVELO JOBS ───────────────────────────────────────────────────────────────
# These Jobs are implemented to keep better backwards copability.
# They pass file descriptors instead of fulll pahts to subprocess


class MARVELOJob(ExecutableJob):
    """Same as ExecutableJob but passes file descriptors to be executable instead
    of paths to fifo pipes. 
    """

    def generate_command(self, root, seperate_job_pipes):
        path = root
        command = self.EXECUTABLE.split()

        if self.PARAMETERS:
            command.extend(self.PARAMETERS.split())

        FDs = []

        for pipe in self.inputs:
            if seperate_job_pipes:
                path = f"{path}/fifo/{self.id}/{pipe.id}.fifo"
            else:
                path = f"{path}/fifo/{pipe.id}.fifo"
            FD = os.open(path, os.O_RDONLY)
            FDs.append(FD)
            command.extend([self.INPUT_FLAG, f"{FD}"])

        for pipe in self.outputs:
            if seperate_job_pipes:
                path = f"{path}/fifo/{self.id}/{pipe.id}.fifo"
            else:
                path = f"{path}/fifo/{pipe.id}.fifo"
            FD = os.open(path, os.O_WRONLY)
            FDs.append(FD)
            command.extend([self.OUTPUT_FLAG, f"{FD}"])
        return (command, FDs)

    def run(self, root, command, redirect_stdout_stderr=False):
        """Run generated command in subprocess
        """
        command, FDs = command

        if redirect_stdout_stderr:
            logger.debug(
                f"Redirecting stderr and stdout to {redirect_stdout_stderr}.")
            redirect = redirect_stdout_stderr.writer
        else:
            redirect = subprocess.PIPE

        logger.debug(f"{self} executing {command}")
        proc = subprocess.Popen(
            command, cwd=f"{root}/{self.id}", stdout=redirect, stderr=redirect, pass_fds=FDs, 
            universal_newlines=True, bufsize=1, shell=False)

        return proc


class DynamicMARVELOJob(MARVELOJob):
    def __init__(self, dependencies, executable, parameters='', groups='', input_flag='-i', output_flag='-o', head=False, inputs=None, outputs=None):

        super().__init__(inputs=inputs, outputs=outputs)

        self.DEPENDENCIES = dependencies
        self.EXECUTABLE = executable
        self.PARAMETERS = parameters

        self.HEAD = head

        self.INPUT_FLAG = input_flag
        self.OUTPUT_FLAG = output_flag

        if groups != '':
            self.GROUPS = groups

# ─── LOCAL JOBS ─────────────────────────────────────────────────────────────────
# These Jobs are meant to be run direcly on the Client machine
# Can be used for collecting data or spawning Jobs with live input


class LocalJob(BaseJob):
    GROUPS = "LOCAL"


class InteractiveJob(LocalJob, PythonJob):
    def run(self):
        path = Path("/tmp/fission/interactive/")
        os.makedirs(path, exist_ok=True)
        pipe = f"{self.id}.fifo"
        if (path/pipe).exists():
            os.remove(path/pipe)
        os.mkfifo(path/pipe)
        logger.info("Starting interactive Terminal")
        proc = subprocess.Popen(
            f'lxterminal --command="fission_interactive.py -p {path/pipe} -n \\"{self}\\""',
            preexec_fn=os.setsid, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        fd = open(path/pipe, 'r')
        while True:
            data = fd.readline()[:-1]
            if not data:
                yield None
            yield data


class CSVSinkJob(LocalJob, PythonJob):
    def __init__(self, path, inputs=None, col_pattern="pipe_{pipe.id}"):
        self.path = path
        self.col_pattern = col_pattern

        super().__init__(inputs=inputs)

    def setup(self, *args, **kwargs):
        self.file = open(self.path, "w", newline='')

        fieldnames = [self.col_pattern.format(
            pipe=pipe, job=self) for pipe in self.inputs]

        self.writer = csv.writer(
            self.file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.writer.writerow(fieldnames)

        return super().setup(*args, **kwargs)

    def run(self, *args):
        self.writer.writerow([str(item) for item in args])
        self.file.flush()

# ────────────────────────────────────────────────────────────────────────────────


class Head():
    def __init__(self, head, head_length):
        """
        Bitwise Operation on head, like slicing, indexing or setting a bit

        Arguments:
            head {int,bytes} -- Head can be given in bytes or in int
            head_length {int} -- Is the length of head, counted in bytes
        """
        self._head = head
        self._head_length = head_length

    # Setting value bitwise
    def __setitem__(self, index, value):
        if index >= 0:
            if index == 1 and value == 1:
                raise ValueError("Bit is not allowed to set")
            else:
                if index > self._head_length*8-1:
                    raise IndexError("Index is out of range")
        else:
            if index == self._head_length*8*(-1)+1 and value == 1:
                raise ValueError("Bit is not allowed to set")
            else:
                if index < self._head_length*8*(-1):
                    raise IndexError("Index is out of range")

        result = 0
        set_l = self.bit_conversion
        set_l[index] = value

        for i in range((len(set_l))):
            result += set_l[i]*2**((len(set_l)-1)-i)

        self._head = result

    def __getitem__(self, key):
        if isinstance(self._head, bytes):
            head_int = self.bytes_int(bytes)
        else:
            head_int = self._head

        if isinstance(key, slice):
            start, stop, step = key.indices(len(self)*8)
            result = 0

            slicing = []

            slicing = self.bit_conversion[key]

            for i in range((len(slicing))):
                result += slicing[i]*2**((len(slicing)-1)-i)
            return Head(result, len(self))

        else:
            if isinstance(key, int):
                if key >= 0:
                    if key > self._head_length*8-1:
                        raise IndexError("Index is out of range")
                    else:
                        if head_int & (1 << (self._head_length*8-1)-key):
                            return True
                        else:
                            return False
                else:
                    if key < self._head_length*8*(-1):
                        raise IndexError("Index is out of range")
                    else:
                        if head_int & (1 << (key*(-1)-1)):
                            return True
                        else:
                            return False

    def __len__(self):
        return (self._head_length)

    @property
    def bit_conversion(self):
        bit_c = []
        if isinstance(self._head, bytes):
            head_int = self.bytes_int(bytes)
        else:
            head_int = self._head
        for i in range((self._head_length*8)):
            if head_int & (1 << ((self._head_length*8-1)-i)):
                bit_c.append(1)
            else:
                bit_c.append(0)
        return bit_c

    # Conversion from int to Bytes
    def int_bytes(self, value, length):
        result = []
        for i in range(0, length):
            result.append(value >> (i * 8) & 0xff)
        result.reverse()
        return result

    # Conversion from bytes to int
    def bytes_int(self, bytes):
        result = 0
        for b in bytes:
            result = result * 256 + int(b)
        return result

    # Return headsize
    @property
    def head_size(self):
        return self._head_length

    # Change headsize (Reduce of Bytes or add Bytes of Zeros)
    @head_size.setter
    def head_size(self, number):
        if isinstance(number, int):
            if number > 0:
                if number + self.head_size <= 4:
                    b = bytearray(self.int_bytes(self._head, self.head_size))
                    for i in range(number):
                        b.append(0)
                    self._head_length = len(b)
                    self._head = self.bytes_int(b)
            else:
                # Reduce number of Bytes
                if (number*(-1) < self.head_size):

                    c = self.int_bytes(self._head, self.head_size)
                    c = c[0:self.head_size-(number*(-1))]
                    self._head_length = len(c)
                    self._head = self.bytes_int(c)
                else:
                    # Head has atleast size of 1 Byte
                    c = self.int_bytes(self._head, self.head_size)
                    c = c[0:1]
                    self._head = self.bytes_int(c)
                    self._head_length = 1

    # Return Head
    @property
    def head(self):
        return self._head

    def to_bytes(self, *args, **kwargs):
        return self.head.to_bytes(*args, **kwargs)

    def __and__(self, other):
        if isinstance(other, int):
            return Head(self.head & other, len(self))
        elif isinstance(other, Head):
            return Head(self.head & other.head, len(self))
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __or__(self, other):
        if isinstance(other, int):
            return Head(self.head | other, len(self))
        elif isinstance(other, Head):
            return Head(self.head | other.head, len(self))
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __xor__(self, other):
        if isinstance(other, int):
            return Head(self.head ^ other, len(self))
        elif isinstance(other, Head):
            return Head(self.head ^ other.head, len(self))
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __lshift__(self, other):
        if isinstance(other, int):
            return Head(self.head << other, len(self))
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __rshift__(self, other):
        if isinstance(other, int):
            return Head(self.head >> other, len(self))
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __invert__(self):
        return Head(~ self.head, len(self))

    def __eq__(self, other):
        if isinstance(other, int):
            return self.head == other
        elif isinstance(other, Head):
            return self.head == other.head
        else:
            raise TypeError(f"Can't compare {type(self)} with {type(other)}")

    def __str__(self):
        return "HEAD: {:0{padding}b}".format(self.head, padding=len(self)*8)

    def __repr__(self):
        return str(self)
