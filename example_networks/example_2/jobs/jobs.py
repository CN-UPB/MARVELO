from fission.core.jobs import PythonJob

class MiddleJob(PythonJob):
    def run(self, a, b):
        value = int(a) + int(b)
        print(f"MiddleJob: {value}")
        return tuple([value]*2)