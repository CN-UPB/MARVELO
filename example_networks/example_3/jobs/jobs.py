from fission.core.jobs import PythonJob
import time

class SourceJob(PythonJob):
	def __init__(self, inputs = None, outputs = None):
		super().__init__(inputs = inputs, outputs = outputs)
		
		
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		
	
	def run(self):
		value = 0
		while True:
			print(f"SourceJob: {value}")
			yield tuple([value])
			time.sleep(1)
			value += 1
			
			
class MiddleJob(PythonJob):
	
	def run(self, input1, input2, input3):
		val = 0
		if input3 == '+':
			value = int(input1) + int(input2)
		elif input3 == '-':
			value = int(input1) - int(input2)
		else:
			val = f"Illegal Operation {input3}"
			
		print(f"MiddleJob: {val}")
		return tuple([val])
		
