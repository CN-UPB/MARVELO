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
		self.soundFile = soundFile
		super().__init__(outputs=outputs)


	def run(self):
		while(True):
			file = self.soundFile
			sampleRate, data = wavfile.read(file)
			print(f"read {file} done") 
			#data = data[2048:4096]
			yield tuple([data])
			time.sleep(10)


class cov1svd(PythonJob):
	def run(self, audio1, audio2):
		audio1 = audio1[:50000] / 255.0 - 0.5  # uint8 takes values from 0 to 255
		audio2 = audio2[:50000] / 255.0 - 0.5  # uint8 takes values from 0 to 255

		samplingRate = 8000
		wavfile.write('rxcov1.wav', samplingRate, audio1[:50000])
		wavfile.write('rxcov2.wav', samplingRate, audio2[:50000])

		x = [audio1, audio2]
		cov = np.cov(x)
		d, E = LA.eigh(cov)
		D = np.diag(d)
		E = E.copy(order='C')
		
		print("cov1svd done")
		return (D, E, np.array(x).reshape(1,-1))
	
	
class sqrtfn(PythonJob):

	def run(self, input1):
		D_r = input1
		D = D_r.reshape((2, 2))
		Di = LA.sqrtm(LA.inv(D))

		print("sqrtfn done")
		return tuple([Di])
		

class whiten(PythonJob):

	def run(self, input1, input2, input3):
		Di_r = input1
		Di = Di_r.reshape((2, 2))

		E = input2
		E = E.reshape((2,2))

		x_r = input3
		x = x_r.reshape((2,-1))

		samplingRate = 8000
		wavfile.write('rxwhiten1.wav', samplingRate, x[0])
		wavfile.write('rxwhiten2.wav', samplingRate, x[1])

		xn = np.dot(Di, np.dot(np.transpose(E), x))
		
		print("whiten done")
		return (xn.reshape(1,-1), xn.reshape(1,-1))

	
class normfn(PythonJob):
	def run(self, input1):
		xn = input1
		xn = xn.reshape((2, -1))

		norm_xn = LA.norm(xn, axis=0)
		norm = [norm_xn, norm_xn]

		print("normfn done")
		return  tuple([np.array(norm).reshape(1,-1)])
	
		
class cov2svd(PythonJob):
	def run(self, input1, input2):
		norm = input1
		norm=norm.reshape(2,-1)

		xn = input2
		xn=xn.reshape(2,-1)

		cov2 = np.cov(np.multiply(norm, xn))
		d_n, Y = LA.eigh(cov2)

		source = np.dot(np.transpose(Y), xn)

		samplingRate = 8000
		wavfile.write('estimated1.wav', samplingRate, source[0])
		wavfile.write('estimated2.wav', samplingRate, source[1])
		
		print("cov2svd done")
		
		return None

