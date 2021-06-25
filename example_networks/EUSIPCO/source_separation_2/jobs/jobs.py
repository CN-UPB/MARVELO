from fission.core.jobs import PythonJob
import time
import os,sys
import argparse
import numpy as np
from scipy.io import wavfile
from scipy import linalg as LA

PATH = '/home/pi'
PACKETSIZE = 4096

class ica_readModule(PythonJob):
	def __init__(self, soundFile, outputs = None):
		self.soundfile = soundFile
		super().__init__(outputs=outputs)
		
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.counter = 0
		sampleRate, self.data = wavfile.read(self.soundfile)

	def run(self):
		while(True):
			if self.counter > 50000/1024:
				print(f"read {self.soundfile} completely done")
				self.counter = 0
				yield 1
				time.sleep(10)
			else:
				i = self.counter
				data2048 = self.data[i*1024:i*1024 + 1024]
				print(f"read {self.soundfile} done")
				yield tuple([data2048])
				self.counter += 1


class cov1svd(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.soundfile1 = np.zeros(0)
		self.soundfile2 = np.zeros(0)

	def run(self, audio1, audio2):
		if(type(audio1) == int or type(audio2) == int):
			samplingRate = 8000
			wavfile.write('rxcov1.wav', samplingRate, self.soundfile1)
			wavfile.write('rxcov2.wav', samplingRate, self.soundfile2)
			print("cov1svd completely done")
			return 1
		else:
			audio1 = audio1[:2048] / 255.0 - 0.5  # uint8 takes values from 0 to 255
			audio2 = audio2[:2048] / 255.0 - 0.5  # uint8 takes values from 0 to 255

			x = [audio1, audio2]
			cov = np.cov(x)
			d, E = LA.eigh(cov)
			D = np.diag(d)
			E = E.copy(order='C')
		
			self.soundfile1 = np.append(self.soundfile1,audio1)
			self.soundfile2 = np.append(self.soundfile2,audio2)
		
			print("cov1svd done")
			return (D, E, np.array(x).reshape(1,-1))
	
	
class sqrtfn(PythonJob):

	def run(self, input1):
		if type(input1) == int:
			print("sqrtfn completely done")
			return 1
		else:
			D_r = input1
			D = D_r.reshape((2, 2))
			Di = LA.sqrtm(LA.inv(D))

			print("sqrtfn done")
			return tuple([Di])
		

class whiten(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.soundfile1 = np.zeros(0)
		self.soundfile2 = np.zeros(0)


	def run(self, input1, input2, input3):
		if type(input1) == int or type(input2) == int or type(input3) == int:
			samplingRate = 8000
			wavfile.write('rxwhiten1.wav', samplingRate, self.soundfile1)
			wavfile.write('rxwhiten2.wav', samplingRate, self.soundfile2)
			print("whiten completely done")
			return 1
		else:
			Di_r = input1
			Di = Di_r.reshape((2, 2))

			E = input2
			E = E.reshape((2,2))

			x_r = input3
			x = x_r.reshape((2,-1))
		
			self.soundfile1 = np.append(self.soundfile1,x[0])
			self.soundfile2 = np.append(self.soundfile2,x[1])
		
			xn = np.dot(Di, np.dot(np.transpose(E), x))
		
		print("whiten done")
		return (xn.reshape(1,-1), xn.reshape(1,-1))

	
class normfn(PythonJob):
	def run(self, input1):
		if type(input1) == int:
			print("normfn completely done")
			return 1
		else:
			xn = input1
			xn = xn.reshape((2, -1))

			norm_xn = LA.norm(xn, axis=0)
			norm = [norm_xn, norm_xn]

			print("normfn done")
			return  tuple([np.array(norm).reshape(1,-1)])
	
		
class cov2svd(PythonJob):
	def setup(self, *args, **kwargs):
		super().setup(*args, **kwargs)
		self.soundfile1 = np.zeros(0)
		self.soundfile2 = np.zeros(0)

	def run(self, input1, input2):
		if type(input1) == int or type(input2) == int:
			samplingRate = 8000
			wavfile.write('estimated1.wav', samplingRate, self.soundfile1)
			wavfile.write('estimated2.wav', samplingRate, self.soundfile2)
			print("cov2svd completely done")
			return None
		else:	
			norm = input1
			norm=norm.reshape(2,-1)

			xn = input2
			xn=xn.reshape(2,-1)

			cov2 = np.cov(np.multiply(norm, xn))
			d_n, Y = LA.eigh(cov2)

			source = np.dot(np.transpose(Y), xn)

			self.soundfile1 = np.append(self.soundfile1,source[0])
			self.soundfile2 = np.append(self.soundfile2,source[1])
		
			print("cov2svd done")
		
			return None

