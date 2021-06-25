from fission.core.jobs import PythonJob, LocalJob
from shared.jobs.jobs import LoggingJob
from demo_DXCP.py_modules.dxcp_phat import DXCPPhaT

import time
import numpy as np
from scipy.io import wavfile


PATH = '/home/pi'

class read_data(LoggingJob):
	"""
	Source Job of the DXCP overlay network.
	Reads in a soundfile and sends it divided into packets via the output pipes
	
	Attributes:
		soundfile_path {str} -- Describes the path to the soundfile that should be read
		samples_per_packet {int} -- The number of samples that are sended in one packet
		self.data_read {bool} --
		self.end {bool} --
		self.sample_counter {int} --
		self.x {np.array} --
		self.nr_samples {int} --
	"""
	
	def init_job(self, soundfile_path, samples_per_packet = 2048):
		"""
		Initializes the Job.

		Arguments:
			soundfile_path {str} -- Describes the path to the soundfile that should be read		
		samples_per_packet {int} -- Sets the number of samples that are sended in a packet (default: {2048})
		"""
		self.soundfile_path = soundfile_path
		self.samples_per_packet = samples_per_packet

	def setup_job(self):
		"""
		Setups all attributes before executing the job
		"""
		self.data_read = False
		self.end = False
		self.sample_counter = 0
		

	def run_job(self):
		"""
		Execution of the job
		Has no inputs since it is a source job
		"""
		if self.end:
			print(f'read_data completely done')
			time.sleep(30)
			self.setup_job()
		
		if not self.data_read:
			_, data = wavfile.read(self.soundfile_path)
			data_norm = np.vstack((data[:, 0], data[:, 1]))/np.max(np.abs(np.hstack((data[:, 0], data[:, 1]))))
			data_norm_max = np.max(np.abs(np.hstack((data_norm[:, 0], data_norm[:, 1]))))
			
			self.x = data_norm.transpose()
			self.nr_samples, nr_channel = self.x.shape
			self.data_read = True
			
		
		num_samples = self.samples_per_packet
		size_loop = int(self.nr_samples/num_samples)		
		counter = self.sample_counter
		
		outputData = self.x[np.arange(counter*num_samples, (counter+1)*num_samples), :]
		outputData_0 = outputData[:, 0].copy(order='C')
		outputData_1 = outputData[:, 1].copy(order='C')
		
		self.sample_counter += 1
		
		if size_loop == self.sample_counter:
			self.end = True
				
		time.sleep(0.1)			
	
		return (outputData_0, outputData_1)
		


class dxcp_phat(LoggingJob):
	"""
	The core computation of the overlay network
	
	Attributes:
		Inst_DXCPPhaT {DXCPPhat} -- Instance of DXCPPhat 
	
	"""
	def init_job(self):
		return None
	

	def setup_job(self):
		"""
		Setups all attributes before executing the job
		"""
		self.Inst_DXCPPhaT = DXCPPhaT()

	def run_job(self, input0, input1):
		"""
		Execution of the job
		
		Arguments:
			input0 {np_array} -- Samples of the first audio track
			input1 {arraylike} -- Samples of the second audio track	
			
		Returns:
			tuple -- first element SROppm_est_out, second element TimeOffsetEndSeg_est_out
		
		"""
		
		num_samples = len(input0)
		inputData = np.zeros((num_samples, 2))
		inputData[:, 0] = input0  # x_1_ell
		inputData[:, 1] = input1  # x_2_ell

		OutputDXCPPhaT = self.Inst_DXCPPhaT.process_data(inputData)

    		# set output vectors of this wrapper-function
		SROppm_est_out = np.float32(OutputDXCPPhaT['SROppm_est_out'])
		TimeOffsetEndSeg_est_out = np.float32(OutputDXCPPhaT['TimeOffsetEndSeg_est_out'])
		# write output data into pipes
		outputData = np.array([SROppm_est_out, TimeOffsetEndSeg_est_out], dtype=np.float32)
		
		return (outputData[0], outputData[1])


class print_results(LoggingJob, LocalJob):
	"""
	Sink job of the overlay network
	Stores the results in an .txt file
	"""
	def init_job(self):
		return None
	
	def setup_job(self):
		"""
		Setups all attributes before executing the job
		"""
		self.pktCntr= 0
		self.cnt_seg = 1
		self.text_file = open("dxcp_results.txt", "w")


	def run_job(self, input0, input1):
		"""
		Execution of the Job
		
		Arguments:
			input0 {float} -- SROppm_est_out
			input1 {float} -- TimeOffsetEndSeg_est_out
		"""
             	# for the length of the input signal of 15000 -> 120 s, 8000 -> 64 s
		ResetPeriod_NumFrInp = 0     # for parameters of DXCP-PhaT-CL estimator: ResetPeriod_sec=30 and FFTshift_dxcp = 2**12
	
		if self.pktCntr >= ResetPeriod_NumFrInp:
			print(f'Past-Seg: SRO_ppm = {input0}; TimeOffset_smp = {input1}')
			self.text_file.write(f'Past-Seg: SRO_ppm = {input0}; TimeOffset_smp = {input1};')
			self.pktCntr = 0
		else:
			self.pktCntr += 1
			
		return None



