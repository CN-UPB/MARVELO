from fission.core.jobs import PythonJob

from time import sleep

class SourceJob(PythonJob):
    def run(self):
        n = 0
        while True:
            print(n)
            yield tuple([20]* len(self.outputs))
            sleep(1)
            n += 1

class SquaredJob(PythonJob):
    def run(self, a):
        print(a**2)

class DoubleJob(PythonJob):
    def run(self, a):
        print(a*2)

class DiffJob(PythonJob):
    def run(self, a, b):
        print(a - b)