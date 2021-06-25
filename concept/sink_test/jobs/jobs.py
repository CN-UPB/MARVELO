from fission.core.jobs import PythonJob
import time

class SourceJob(PythonJob):
    def __init__(self, outputs, start_value=0):
        self.start_value = start_value
        super().__init__(outputs=outputs)

    def run(self):
        value = self.start_value
        while True:
            print(value)
            yield tuple([value]*len(self.outputs))
            time.sleep(.5)
            value += 1
