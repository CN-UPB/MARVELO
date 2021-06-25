from fission.core.jobs import PythonJob, LocalJob
import time
import os,sys
import csv
import argparse
import numpy as np
from scipy.io import wavfile
from scipy import linalg as LA
import psutil


PATH = '/home/pi'
PACKETSIZE = 500
DATASIZE = 50000

NO_ACTION = 0
RESTART = 1

class ica_readModule(PythonJob):

	GROUPS = "Node1"

	def __init__(self, soundFile, inputs=None, outputs = None):
		self.soundfile = soundFile
		super().__init__(inputs = inputs, outputs=outputs)
		
	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		self.counter = 0
		self.restart_counter = 0
		self.sending_done = False
		sampleRate, self.data = wavfile.read(self.soundfile)
		self.data = np.append(self.data, np.zeros(PACKETSIZE))
		
		return super().setup(*args, **kwargs)
		

	def run(self, input):
		time_in = time.time_ns()
		
		self.restart_counter += 1
		
		if self.restart_counter >= 450:
			time.sleep(1)
			self.counter = 0
			self.restart_counter = 0
			self.sending_done = False
			
			log_arr = ["ica_readmodule", self.p.pid, 1, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return(RESTART, log_arr)
		
		
		if self.sending_done:
			log_arr = ["ica_readmodule", self.p.pid, 2, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)
		
		elif self.counter >= DATASIZE/PACKETSIZE:
			self.counter = 0
			self.sending_done = True
				
			log_arr = ["ica_readmodule", self.p.pid, 2, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)
		else:
			begin = self.counter*PACKETSIZE
			end = begin + PACKETSIZE
			data = self.data[begin:end]
			self.counter += 1
			#print(f"send packet of {self.soundfile} ", f"{self.counter}/{(DATASIZE/PACKETSIZE)}")
			
			log_arr = ["ica_readmodule", self.p.pid, 1, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (data, log_arr)

class cov1svd(PythonJob):

	#DEFAULT_NODE = "192.168.0.28"

	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		
		self.audio1 = np.zeros(0)
		self.audio2 = np.zeros(0)
		self.x = np.zeros(0)
		self.state = 0
		self.counter = 0
		
		return super().setup(*args, **kwargs)

	def run(self, audio1, audio2):
		time_in = time.time_ns()
		
		if self.state == 0 and type(audio1) != int and type(audio2) != int:
			''' RECEIVING '''
			self.audio1 = np.append(self.audio1, (audio1 / 255.0 - 0.5))
			self.audio2 = np.append(self.audio2, (audio2 / 255.0 - 0.5))
			
			if len(self.audio1) >= DATASIZE and len(self.audio2) >= DATASIZE:
				self.state = 1
				
				samplingRate = 8000
				wavfile.write('rxcov1.wav', samplingRate, self.audio1)
				wavfile.write('rxcov2.wav', samplingRate, self.audio2)
			
				x = [self.audio1, self.audio2]
				cov = np.cov(x)
				d, E = LA.eigh(cov)
				D = np.diag(d)
				#E = E.copy(order='C')
				
				self.x = np.array(x).reshape(1,-1)[0]
				print("cov1svd done")
				
				log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
				return (D, E, NO_ACTION, log_arr)
			else:
			
				log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
				return (NO_ACTION, NO_ACTION, NO_ACTION, log_arr)
			
		elif self.state == 1:
			''' SENDING '''
			begin = self.counter*PACKETSIZE
			end = begin + PACKETSIZE
			self.counter += 1
			if self.counter >= 2*DATASIZE/PACKETSIZE:
				self.state = 2
				
			#print("cov1svd send packet", f"{self.counter}/{(2*DATASIZE/PACKETSIZE)}")

			log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, NO_ACTION, self.x[begin:end], log_arr)
			
		else:	
			''' IDLE '''
			if type(audio1) == int: 
				if audio1 == RESTART:
					self.audio1 = np.zeros(0)
					self.audio2 = np.zeros(0)
					self.x = np.zeros(0)
					self.state = 0
					self.counter = 0
					log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
					return (RESTART,RESTART,RESTART, log_arr)	
			
			log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, NO_ACTION, NO_ACTION, log_arr)
		
class cov1svd_sqrtfn(PythonJob):

	GROUPS = "Node2"

	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		
		self.audio1 = np.zeros(0)
		self.audio2 = np.zeros(0)
		self.x = np.zeros(0)
		self.state = 0
		self.counter = 0
		
		return super().setup(*args, **kwargs)

	def run(self, audio1, audio2):
		time_in = time.time_ns()
		
		if self.state == 0 and type(audio1) != int and type(audio2) != int:
			''' RECEIVING '''
			self.audio1 = np.append(self.audio1, (audio1 / 255.0 - 0.5))
			self.audio2 = np.append(self.audio2, (audio2 / 255.0 - 0.5))
			
			if len(self.audio1) >= DATASIZE and len(self.audio2) >= DATASIZE:
				self.state = 1
				
				samplingRate = 8000
				wavfile.write('rxcov1.wav', samplingRate, self.audio1)
				wavfile.write('rxcov2.wav', samplingRate, self.audio2)
			
				x = [self.audio1, self.audio2]
				cov = np.cov(x)
				d, E = LA.eigh(cov)
				D = np.diag(d)
				#E = E.copy(order='C')
				
				self.x = np.array(x).reshape(1,-1)[0]
				print("cov1svd done")
				
				D_r = D
				D = D_r.reshape((2, 2))
				Di = LA.sqrtm(LA.inv(D))
				
				
				
				log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
				return (Di, E, NO_ACTION, log_arr)
			else:
			
				log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
				return (NO_ACTION, NO_ACTION, NO_ACTION, log_arr)
			
		elif self.state == 1:
			''' SENDING '''
			begin = self.counter*PACKETSIZE
			end = begin + PACKETSIZE
			self.counter += 1
			if self.counter >= 2*DATASIZE/PACKETSIZE:
				self.state = 2
				
			#print("cov1svd send packet", f"{self.counter}/{(2*DATASIZE/PACKETSIZE)}")

			log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, NO_ACTION, self.x[begin:end], log_arr)
			
		else:	
			''' IDLE '''
			if type(audio1) == int: 
				if audio1 == RESTART:
					self.audio1 = np.zeros(0)
					self.audio2 = np.zeros(0)
					self.x = np.zeros(0)
					self.state = 0
					self.counter = 0
					log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
					return (RESTART,RESTART,RESTART, log_arr)	
			
			log_arr = ["cov1svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, NO_ACTION, NO_ACTION, log_arr)
	
class sqrtfn(PythonJob):

	#GROUPS = "Node2"

	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		
		return super().setup(*args, **kwargs)
	

	def run(self, input1):
		time_in = time.time_ns()
		
		if type(input1) != int:
			D_r = input1
			D = D_r.reshape((2, 2))
			Di = LA.sqrtm(LA.inv(D))

			print("sqrtfn done")	
			log_arr = ["sqrtfn", self.p.pid, 1, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (Di, log_arr)
	
		log_arr = ["sqrtfn", self.p.pid, 1, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
		return (NO_ACTION, log_arr)
			
		

class whiten(PythonJob):

	GROUPS = "Node2"
	
	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		
		self.audio = np.zeros(0)
		self.E = np.zeros(0)
		self.Di = np.zeros(0)
		self.xn = np.zeros(0)
		self.Di_recv = False
		self.E_recv = False
		self.state = 0
		self.counter = 0
		
		return super().setup(*args, **kwargs)

	def run(self, input1, input2, input3):
		time_in = time.time_ns()
		
		if self.state == 0:
			''' RECEIVING '''
			if type(input1) != int:
				self.Di = input1
				self.Di_recv = True
				#print("whiten received Di")
			if type(input2) != int:
				self.E = input2
				self.E_recv = True
				#print("whiten received E")
			if type(input3) != int:
				self.audio = np.append(self.audio, input3)
				
				if self.Di_recv and self.E_recv and len(self.audio) >= DATASIZE*2:
					Di_r = self.Di
					Di = Di_r.reshape((2, 2))

					E = self.E
					E = E.reshape((2,2))

					x_r = self.audio
					x = x_r.reshape((2,-1))
		
					samplingRate = 8000
					wavfile.write('rxwhiten1.wav', samplingRate, x[0])
					wavfile.write('rxwhiten2.wav', samplingRate, x[1])
		
					xn = np.dot(Di, np.dot(np.transpose(E), x))
			
					self.state = 1
					self.xn = xn.reshape(1,-1)[0]
					print("whiten done")
			
			
			log_arr = ["whiten", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)
					
		elif self.state == 1:
			''' SENDING '''
			begin = self.counter*PACKETSIZE
			end = begin + PACKETSIZE
			self.counter += 1
			if self.counter >= 2*DATASIZE/PACKETSIZE:
				self.state = 2
			
			#print("whiten sendet packet", f"{self.counter}/{(2*DATASIZE/PACKETSIZE)}")	
			
			log_arr = ["whiten", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (self.xn[begin:end], log_arr)
		
		else:
			''' IDLE '''
			if type(input3) == int: 
				if input3 == RESTART:
					self.audio = np.zeros(0)
					self.E = np.zeros(0)
					self.Di = np.zeros(0)
					self.xn = np.zeros(0)
					self.Di_recv = False
					self.E_recv = False
					self.state = 0
					self.counter = 0
					log_arr = ["whiten", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
					return (RESTART, log_arr)
			
			log_arr = ["whiten", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)

	
class normfn(PythonJob):

	GROUPS = "Node3"
	
	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		self.audio = np.zeros(0)
		self.norm = np.zeros(0)
		self.state = 0
		self.counter = 0

		return super().setup(*args, **kwargs)

	def run(self, input1):
		time_in = time.time_ns()
		if self.state == 0 and type(input1) != int:
			''' RECEIVING '''
			self.audio = np.append(self.audio, input1)
			
			if len(self.audio) >= DATASIZE*2:
				xn = self.audio
				xn = xn.reshape((2, -1))

				norm_xn = LA.norm(xn, axis=0)
				self.norm = np.array([norm_xn, norm_xn]).reshape(1,-1)[0]

				print("normfn done")
				self.state = 1
				
				
			log_arr = ["normfn", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)
			
			
		elif self.state == 1:
			''' SENDING '''
			begin = self.counter*PACKETSIZE
			end = begin + PACKETSIZE
			self.counter += 1
			
			if self.counter >= 2*DATASIZE/PACKETSIZE:
				self.state = 2
				
			#print("normfn sended packet", f"{self.counter}/{(2*DATASIZE/PACKETSIZE)}")
			
			log_arr = ["normfn", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (self.norm[begin:end], log_arr)
			
		else:
			''' IDLE '''
			if type(input1) == int :
				if input1 == RESTART:
					self.audio = np.zeros(0)
					self.norm = np.zeros(0)
					self.state = 0
					self.counter = 0
					log_arr = ["normfn", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
					return (RESTART, log_arr)
			log_arr = ["normfn", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return (NO_ACTION, log_arr)
			
	
		
class cov2svd(PythonJob):

	GROUPS = "Node3"

	def setup(self, *args, **kwargs):
		self.p = psutil.Process()
		
		self.norm = np.zeros(0)
		self.xn = np.zeros(0)
		self.state = 0
		
		return super().setup(*args, **kwargs)

	def run(self, input1, input2):
		time_in = time.time_ns()
		if self.state == 0:
			#print(input1, input2)
			if type(input1) != int:
				self.norm = np.append(self.norm, input1)
			if type(input2) != int:
				self.xn = np.append(self.xn, input2)
	
			if len(self.norm) >= DATASIZE*2 and len(self.xn) >= DATASIZE*2:
				norm = self.norm
				norm=norm.reshape(2,-1)

				xn = self.xn
				xn=xn.reshape(2,-1)

				cov2 = np.cov(np.multiply(norm, xn))
				d_n, Y = LA.eigh(cov2)

				source = np.dot(np.transpose(Y), xn)
				
				samplingRate = 8000
				wavfile.write('estimated1.wav', samplingRate, source[0])
				wavfile.write('estimated2.wav', samplingRate, source[1])
				
				self.state = 2
				print("cov2svd completely done")
			
			log_arr = ["cov2svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return tuple([log_arr])
				
		else:
			'''IDLE'''
			if type(input1) == int:
				if input1 == RESTART:
					self.norm = np.zeros(0)
					self.xn = np.zeros(0)
					self.state = 0
					print("RESTART")
			
			log_arr = ["cov2svd", self.p.pid, self.state, self.p.cpu_percent()/psutil.cpu_count(), self.p.memory_percent(), time_in, time.time_ns()]
			return tuple([log_arr])
			
class CSVSinkJob_2(PythonJob, LocalJob):

	def __init__(self, path, inputs=None, col_pattern="pipe_{pipe.id}"):
		self.path = path
		self.col_pattern = col_pattern

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
		

        
        
class DistributingJob(PythonJob):
    GROUPS = "Node3"
    def run(self, input):
        return tuple([input, input])

