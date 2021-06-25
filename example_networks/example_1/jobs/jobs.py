from fission.core.jobs import PythonJob
import time

class SourceJob(PythonJob):
    def run(self):
        value = 0
        while True:
            print(f"SourceJob: {value}")
            yield tuple([value])
            time.sleep(1)
            value += 1 

class MiddleJob(PythonJob):
    def run(self, value):
        print(f"MiddleJob: {value}")
        return tuple([value])
