from fission.core.jobs import PythonJob
import some_network.jobs.my_module as my_module
import time

class SumJob(PythonJob):
    DEPENDENCIES = [my_module]
    HEAD = True
    def run(self, a):
        print(a)
        print(self.in_heads)
        with open(f"{self.id}.txt", "a") as f:
            f.write(f"{a}\n")

class SourceJob(PythonJob):
    DEPENDENCIES = [my_module]
    def run(self):
        value = 0
        while True:
            print(value)
            yield my_module.A(value)
            time.sleep(.5)
            value += 1 
