from fission.core.jobs import PythonJob
import time
import os,sys
import argparse
import numpy as np
from scipy.io import wavfile
from scipy import linalg as LA

PATH = '/home/pi'
PACKETSIZE = 1028
DONE = 1
NO_ACTION = 0

class ica_readModule(PythonJob):
	def __init__(self, soundFile, outputs = None):
		self.soundfile = soundFile
		super().__init__(outputs=outputs)
		
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.counter = 0
		sampleRate, self.data = wavfile.read(self.soundfile)
		self.data = np.append(self.data, np.zeros(PACKETSIZE))

	def run(self):
		while(True):
			if self.counter > len(self.data)/PACKETSIZE:
				print(f"sended all packets of {self.soundfile}")
				self.counter = 0
				yield DONE
				time.sleep(20)
			else:
				begin = self.counter*PACKETSIZE
				end = begin + PACKETSIZE
				data = self.data[begin:end]
				print(f"send packet of {self.soundfile}")
				yield tuple([data])
				self.counter += 1


class cov1svd(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.audio1 = np.zeros(0)
		self.audio2 = np.zeros(0)

	def run(self, audio1, audio2):
		if(type(audio1) == int or type(audio2) == int):
			samplingRate = 8000
			wavfile.write('rxcov1.wav', samplingRate, self.audio1)
			wavfile.write('rxcov2.wav', samplingRate, self.audio2)
			
			x = [self.audio1, self.audio2]
			cov = np.cov(x)
			d, E = LA.eigh(cov)
			D = np.diag(d)
			E = E.copy(order='C')
			
			print("cov1svd done")
			
			for i in range(0, len(self.audio1)/PACKETSIZE - 1):
				begin = i*PACKETSIZE
				end = begin + PACKETSIZE
				yield ((NO_ACTION, NO_ACTION, np.array(x[begin:end]).reshape(1,-1)))
			return ((D, E, np.array(x[len(self.audio1) - PACKETSIZE:len(self.audio1)]).reshape(1,-1)))
			
		else:
			self.audio1 = np.append(self.audio1, (audio1 / 255.0 - 0.5))
			self.audio2 = np.append(self.audio2, (audio2 / 255.0 - 0.5))

			x = [audio1, audio2]
			cov = np.cov(x)
			d, E = LA.eigh(cov)
			D = np.diag(d)
			E = E.copy(order='C')
		
			self.soundfile1 = np.append(self.soundfile1,audio1)
			self.soundfile2 = np.append(self.soundfile2,audio2)
		
			print("cov1svd packet received")
			
			return NO_ACTION
	
	
class sqrtfn(PythonJob):

	def run(self, input1):
		if type(input1) == int:
			print("sqrtfn no action")
			return NO_ACTION
		else:
			D_r = input1
			D = D_r.reshape((2, 2))
			Di = LA.sqrtm(LA.inv(D))

			print("sqrtfn done")
			return tuple([Di])
		

class whiten(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.audio = np.zeros(0)
		self.E = None
		self.Di = None

	def run(self, input1, input2, input3):
		if type(input1) != int:
			self.Di = input1
			print("whiten received Di")
		if type(input) != int:
			self.E = input2
			print("whiten received E")
		if type(input3) != int:
			self.audio = np.append(self.audio,input3)
			print("whiten received packet")
		
		if self.Di != None and self.E != None and len(self.audio) > 50000*2:
			i_r = self.Di
			Di = Di_r.reshape((2, 2))

			E = self.E
			E = E.reshape((2,2))

			x_r = self.audio
			x = x_r.reshape((2,-1))
		
			samplingRate = 8000
			wavfile.write('rxwhiten1.wav', samplingRate, x[0])
			wavfile.write('rxwhiten2.wav', samplingRate, x[1])
		
			xn = np.dot(Di, np.dot(np.transpose(E), x))
			
			print("whiten done")
			
			for i in range(0, len(xn)/PACKETSIZE):
				begin = i*PACKETSIZE
				end = begin + PACKETSIZE
				yield(xn[begin:end].reshape(1,-1),xn[begin:end].reshape(1,-1))

		return NO_ACTION

	
class normfn(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.audio = np.zeros(0)

	def run(self, input1):
		if type(input1) != int:
			self.audio = np.append(self.audio, input1)
		
		if len(self.audio) > 50000*2:
		
			xn = self.audio
			xn = xn.reshape((2, -1))

			norm_xn = LA.norm(xn, axis=0)
			norm = [norm_xn, norm_xn]

			print("normfn done")
			
			for i in range(0, len(norm)/PACKETSIZE): 
				begin = i*PACKETSIZE
				end = begin + PACKETSIZE
				yield tuple([np.array(norm[begin:end]).reshape(1,-1)])
			
		return NO_ACTION
			
	
		
class cov2svd(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.norm = np.zeros(0)
		self.xn = np.zeros(0)
		

	def run(self, input1, input2):
		if type(input1) != int:
			self.norm = np.append(self.norm, input1)
		if type(input2) != int:
			self.xn = np.append(self.xn, input2)
	
		if len(self.norm) > 50000*2 and len(self.xn) > 50000*2:
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
			print("cov2svd completely done")


