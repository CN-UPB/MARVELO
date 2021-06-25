import atexit
import codecs
import multiprocessing
import os
import shutil
import signal
import sys

from fission.core.jobs import BaseJob, ExecutableJob, MARVELOJob
from fission.core.pipes import BasePipe
from fission.manager import cwd_wrapper
from fission.remote.debug import MultiWrite

PROCESSES = []


def sig_term():
    for proc in PROCESSES:
        proc.terminate()


atexit.register(sig_term)


def emulate(obj, path=".emulate"):
    if isinstance(obj, BasePipe):
        return PipeEmulator(obj)
    elif isinstance(obj, MARVELOJob):
        return ExecutableJobEmulator(obj, root=path)
    elif isinstance(obj, ExecutableJob):
        raise TypeError("Emulation not supported for ExecutableJobs.")
    elif isinstance(obj, BaseJob):
        return JobEmulator(obj, root=path)
    else:
        raise TypeError(f"No emulator found for {type(obj)}")


class PipeEmulator():
    def __init__(self, pipe):
        self.pipe = pipe
        r, w = os.pipe()
        self.reader = open(r, "rb")
        self.writer = open(w, "wb", 0)
        r, w = os.pipe()
        self.mid_reader = open(r, "rb")
        self.mid_writer = open(w, "wb", 0)
        r, w = os.pipe()
        self.end_reader = open(r, "rb")
        self.end_writer = open(w, "wb", 0)

    def put(self, data):
        # Pack data
        packed = self.pipe.pack(data)
        # Write to first pipe (for pipe.write)
        self.pipe.write(self.writer, packed)

        # This simulates what the wrapper does
        # Read from first pipe (for pipe.read_wrapper)
        data = self.pipe.read_wrapper(self.reader)
        # Write data to second pipe
        self.mid_writer.write(data)

    def put_head(self, head):
        # Writing it to second pipe
        # Does not need to be rewritte, only one read
        # function for head
        self.pipe.write_head(self.mid_writer, head)

    def get_head(self):
        return self.pipe.read_head(self.end_reader)

    def get(self):
        out = self.pipe.read(self.end_reader)
        unpacked = self.pipe.unpack(out)
        return unpacked

    def kill(self):
        self.end_reader.close()
        self.end_writer.close()

        self.mid_reader.close()
        self.mid_writer.close()

        self.reader.close()
        self.writer.close()

    def __call__(self, data):
        packed = self.pipe.pack(data)
        print(f"Packed to: {packed}")

        self.pipe.write(self.writer, packed)
        print("Wrote to pipe.")

        wrapper = self.pipe.read_wrapper(self.reader)
        print(f"Read in pipe.read_wrapper: {wrapper}")

        print(f"Rewriting to pipe (not using write method of pipe)...")
        self.end_writer.write(wrapper)

        out = self.pipe.read(self.end_reader)
        print(f"Read in pipe.read: {out}")

        unpacked = self.pipe.unpack(out)
        print(f"Unpacked to: {unpacked}")

        return packed, wrapper, out, unpacked


class JobEmulator():
    def __init__(self, job, root=".emulate", start=True):
        # Create Emulators for inpipes
        in_emulators = []
        for in_pipe in job.inputs:
            in_emulators.append(PipeEmulator(in_pipe))
        self.in_emulators = in_emulators

        # Create Emulators for outpipes
        out_emulators = []
        for out_pipe in job.outputs:
            out_emulators.append(PipeEmulator(out_pipe))
        self.out_emulators = out_emulators

        self.job = job

        self.cwd = f"{root}/{job.id}"

        if os.path.exists(self.cwd):
            shutil.rmtree(self.cwd)

        if self.job.DEPENDENCIES:
            shutil.copytree(self.job.DEPENDENCIES, self.cwd)
        else:
            os.makedirs(self.cwd, exist_ok=True)

        if start:
            self.start()

    def start(self):
        in_files = [p.mid_reader for p in self.in_emulators]
        out_files = [p.end_writer for p in self.out_emulators]

        self.proc = multiprocessing.Process(target=cwd_wrapper, args=(
            self.job.wrapper, self.cwd, in_files, out_files), daemon=True)
        self.proc.start()

    def __call__(self, *args, head=0):
        if len(args) != len(self.in_emulators):
            raise RuntimeError(
                f"Expected {len(self.in_emulators)} arguments, not {len(args)}")

        for emulator, arg in zip(self.in_emulators, args):
            if isinstance(arg, tuple):
                _iter = arg
            else:
                _iter = (arg,)

            for argument in _iter:
                if self.job.HEAD:
                    print(f"Putting head {head} in {emulator.pipe}")
                    emulator.put_head(head)
                print(f"Putting {argument} in {emulator.pipe}.")
                emulator.put(argument)

        outputs = []

        for emulator in self.out_emulators:
            if self.job.HEAD:
                head = emulator.get_head()
                print(f"Got head {head} from {emulator.pipe}")
            out = emulator.get()
            print(f"Got {out} from {emulator.pipe}.")
            outputs.append(out)

        return outputs

    def kill(self):
        self.proc.kill()
        for e in self.in_emulators + self.out_emulators:
            e.kill()


class ExecutableJobEmulator(JobEmulator):
    def __init__(self, job, root='.emulate'):
        super().__init__(job, root=root, start=False)
        command = self.job.EXECUTABLE.split()

        if self.job.PARAMETERS:
            command.extend(self.PARAMETERS.split())

        FDs = []

        for emulator in self.in_emulators:
            FD = emulator.mid_reader.fileno()
            command.extend([job.INPUT_FLAG, f"{FD}"])
            FDs.append(FD)

        for emulator in self.out_emulators:
            FD = emulator.end_writer.fileno()
            command.extend([job.OUTPUT_FLAG, f"{FD}"])
            FDs.append(FD)

        print(f"Command for {self.job}: {command}")

        self.redirect_output = MultiWrite(sys.stdout, daemon=True)
        self.redirect_output.start()

        self.proc = self.job.run(root, (command, FDs),
                                 redirect_stdout_stderr=self.redirect_output)

        PROCESSES.append(self.proc)

    def kill(self):
        self.proc.terminate()
        self.redirect_output.kill()
        stdout, stderr = self.proc.communicate(timeout=5)

        if stdout:
            print(f"STDOUT:\n{stdout.decode('utf-8')}")
        if stderr:
            print(f"STDERR:\n{stderr.decode('utf-8')}")
