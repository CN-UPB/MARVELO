from fission.core.jobs import PythonJob

class SquaredJob(PythonJob):
    def run(self, a):
        print(a**2)

class DoubleJob(PythonJob):
    def run(self, a):
        print(a*2)

class DiffJob(PythonJob):
    def run(self, a, b):
        print(a - b)