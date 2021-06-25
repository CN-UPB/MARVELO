from fission.core.jobs import PythonJob
import time

class MiddleJob(PythonJob):
    HEAD = True

    def run(self, a, b):
        try:
            value = int(a) + int(b)
            if value >= 10:
                self.head = 0b00000001
        except:
            value = f"Please only type ints"
        print(f"MiddleJob: {value}")
        return tuple([value])

class HeadJob(PythonJob):
    HEAD = True

    def run(self, a):
        if self.head & 1 and type(a) == int:
            value = f"Head was set and the result is: {a}"
        elif type(a) == int:
            value = f"No Head. Result: {a}"
        else:
            value = f"Please only type ints"
        print(f"HeadJob: {value}")
        return tuple([value])