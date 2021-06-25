from fission.core.jobs import PythonJob, LocalJob
import time
import csv
import psutil

class SourceJob(PythonJob):
    def __init__(self, start=1, step=1, delay=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = start
        self.step = step
        self.delay = delay

    def run(self):
        while True:
            print(f"{self.id} -> {self.value}")
            yield self.value
            time.sleep(self.delay)
            self.value += self.step
            
class ForwardingJob(PythonJob):
    def run(self, *inputs):
        return inputs
    
class DistributingJob(PythonJob):
    def run(self, input):
        return input
    
class ClockJob(LocalJob, PythonJob):
    def __init__(self, clock_interval = 0.04, outputs=None):
        self.clock_interval = clock_interval

        super().__init__(outputs = outputs)

    def run(self, *args):
        while True:
            yield 1
            time.sleep(self.clock_interval)
            
class LoggingSinkJob(PythonJob, LocalJob):

	def __init__(self, path, inputs=None):
		self.path = path

		super().__init__(inputs=inputs)

	def setup(self, *args, **kwargs):
		self.file = open(self.path, "w", newline='')
		
		fieldnames = ["job", "pid", "state", "cpu_percent", "memory_percent", "time in", "time out"]

		self.writer = csv.writer(self.file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
		self.writer.writerow(fieldnames)
		
		return super().setup(*args, **kwargs)


	def run(self, *args):
		for row in args:
			self.writer.writerow([str(item) for item in row])
			
		self.file.flush()
		
		
class LoggingJob(PythonJob):
	'''
	If you want to log data like the start/end time of a job execution, the cpu utilization and the memory usage of a job, you should inherite from this Job.
	You must add a \"LoggingSinkJob\" to your network, and a PicklePipe from this job to that sink. The pipe to that sink job is handed over by \"loggin_output\" at the __init__ of the LoggingJob.
	You have to implement the methods init_job(), setup_job(), run_job() in the same manner as you would implement the __init__/setup/run methods of a PythonJob.
	If you write a source job, do not use a infinite loop and yield!
	
	Attributes:
		name {str} -- The name as which this job will be listed in the csv file of the LoggingSinkJob
		counter {int} -- Represents how many entry the LoggingJob has already sent to the LogginSinkJob
		p {psutil.Process} -- The psutil process representation of the LoggingJob
	'''
	
	def init_job(self, *args, **kwargs):
		'''
		Implement this method as a normal __init__ method, but wihtout the call to the super class.
		Use it to hand over parameters from the config to your job.
		'''
		
		raise NotImplementedError
		
		
	def setup_job(self, *args, **kwargs):
		'''
		Implement this method as a normal setup method, but wihtout the call to the super class.
		Use it to initialize attributes of your job.
		'''
		
		raise NotImplementedError
		
		
	def run_job(self,*args, **kwargs):
		'''
		Implement this method as a normal run method. You have to return your outputs as a tuple in the end of the method
		'''
		
		raise NotImplementedError	
	
	
	def __init__(self, inputs=None, outputs=None, logging_output=None, name = "", *args, **kwargs):
		'''
		Initializes the job.
		Hand over inputs and outputs as usual.
		Hand over the PicklePipe to the \"LoggingSinkJob\" by the parameter logging_output
		Further parameters will be forwarded to the init_job method
		'''
		
		if outputs == None:
			outputs = [logging_output]
		else:
			outputs.append(logging_output)
			
		self.name = name
		
		self.init_job(*args, **kwargs)
		super().__init__(inputs=inputs, outputs = outputs)
		
		
	def setup(self, *args, **kwargs):
		'''
		Initilizes the attributes of the job. Arguments will be forwarded to the setup_job method
		'''
		
		self.p = psutil.Process()
		self.p.cpu_percent()
		self.counter = 0
		self.setup_job()
		super().setup(*args, **kwargs)
		
		
	def run(self, *args, **kwargs):
		'''
		Logs the start/end time of the job execution, cpu and memory usage.
		Inputs will  be forwarded to the run_job method.
		'''
		
		time_in = time.time()
		output = self.run_job(*args, **kwargs)
		time_out = time.time()
		log_arr = [self.name, self.p.pid, self.counter, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time_out]
		self.counter += 1
		
		if output == None:
			output = tuple([log_arr])
		else:
			lst = list(output)
			lst.append(log_arr)
			output = tuple(lst)
			
		
		return output
	
	
	
	
	
	
	
		
		
