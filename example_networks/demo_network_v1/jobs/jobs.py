from fission.core.jobs import PythonJob
import time


class SourceJob(PythonJob):
    def run(self):
        value = 1
        while True:
            print(f"{self.id} -> {value}")
            yield value
            time.sleep(1)
            value += 1


class JoinJob(PythonJob):
    def run(self, in_1, in_2, in_3):
        result = in_1 * in_2 * in_3
        print(f"{self.id} -> {result}")
        return result


class ReduceJob(PythonJob):
    def run(self, L):
        result = sum(L)
        print(f"{self.id} -> Sum over {L} is {result}")
