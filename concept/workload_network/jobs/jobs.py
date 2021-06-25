from fission.core.jobs import PythonJob, ExecutableJob, InteractiveJob
import socket 
import psutil 
import time
import numpy



# class IpJob(PythonJob):
#     def run(self):
#         ip = socket.gethostbyname(socket.gethostname())
#         while True:
#             print(ip)
#             yield ip
#             time.sleep(.5)
#             ip = socket.gethostbyname(socket.gethostname())

class WorkloadJob(PythonJob):
    def run(self):
        load = psutil.cpu_percent()
        while True:
            #print(load)
            yield tuple([load])
            time.sleep(.5)
            load = psutil.cpu_percent()

class MemoryJob(PythonJob):
    def run(self):
        mem = psutil.virtual_memory()[2]
        while True:
            #print(mem)
            yield tuple([mem])
            time.sleep(.5)
            mem = psutil.virtual_memory()[2]
            
class SumJobWorkload(PythonJob):
    def run(self, a):
        print(f"Workload: {numpy.around(a,2)}%")
        with open(f"{self.id}.txt", "a") as f:
            f.write(f"{a}\n")

class SumJobMemory(PythonJob):
    def run(self, a):
        print(f"Memory used: {numpy.around(a,2)}%")
        with open(f"{self.id}.txt", "a") as f:
            f.write(f"{a}\n")