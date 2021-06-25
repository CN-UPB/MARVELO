from fission.core.jobs import PythonJob
from functools import reduce


class JoinJob(PythonJob):
    def run(self, *args):
        result = reduce(lambda x, y: x*y, args)
        print(f"{self.id} -> {result}")
        return result


class ReduceJob(PythonJob):
    def run(self, L):
        result = sum(L)
        print(f"{self.id} -> Sum over {L} is {result}")