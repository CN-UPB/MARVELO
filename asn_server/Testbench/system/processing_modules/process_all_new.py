import numpy as np
import scipy.io.wavfile
from asntoolbox import Vad
from asntoolbox import CoherenceWelch
from asntoolbox import Delay
from asntoolbox import CoherenceDriftEstimator
from asntoolbox import Resampling
from asntoolbox import ResamplingControl

# Parameters for vad, psd, ...
vad_params = {"EnergySmoothFactor": 0.9, "OvershootFactor": 2.0}
psd_params = {"FFTSize": 8192, "WelchShift": 1024, "WindowType": "Hann"}
delay_params = {"FrameSize": 1024, "Delay": 1024}
cw_params = {"FFTSize": 8192, "CoherenceTimeDelay": 1024, "MaximumSRO": 300, "WelchShift": 1024}
resampling_params = {"SamplingRateOffset": 0, "WindowSize": 20}
rescontrol_params = {"SmoothFactor": 0.99, "UpdateAfterNumObservations": 30}
smoothFac = 0.99

# Init Processing Blocks
Vad_Block = Vad(vad_params)
CW_Block1 = CoherenceWelch(psd_params)
CW_Block2 = CoherenceWelch(psd_params)
Delay_Block1 = Delay(delay_params)
Delay_Block2 = Delay(delay_params)
CoherenceDriftEstimator_Block = CoherenceDriftEstimator(cw_params)
Resampling_Block = Resampling(resampling_params)
ResamplingControl_Block = ResamplingControl(rescontrol_params)

# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_40ppm.wav')
# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_10ppm.wav')
rate, data = scipy.io.wavfile.read('/home/hafifi/Desktop/docPaderborn/asnRepo/p1/Testbench/asn_server_Emulator/asn_server/Testbench/system/readfile_module/AudioData/Audio_2Chan_80ppm.wav')
# rate, data = scipy.io.wavfile.read('AudioData/Audio_2Chan_100ppm.wav')
#
#

# Simulated Processing
# Mic1:DataBlock1 -> Vad_Block => vad_value
# Mic1:DataBlock1 -> PSD_Block1(1) => psd_value1 -> CoherenceDrift(1)
# Mic2:DataBlock2 -> PSD_Block2(1) => psd_value2 -> CoherenceDrift(2)
# CoherenceDrift => Resampling
n = 0
dataLength, channels = data.shape
coEst = 0
print dataLength
packetLen = 1024
while n < dataLength - 5 * 8192:
    # Get Data
    packetNr = 0
    DataBlock1_buff = []
    DataBlock2_buff = []
    delay_DataBlock1_buf = []
    delay_DataBlock2_buf = []
    while packetNr<40:
        DataBlock1 = data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
        DataBlock1_buff=np.append(DataBlock1_buff,DataBlock1)
        DataBlock2_nosync = data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 0]
        #print 'diff at read', sum(DataBlock1-DataBlock2_nosync)
        # ------ Sync Processing - DES ----------
        # Resampling of second stream
        DataBlock2 = Resampling_Block.process_data(DataBlock2_nosync)
        #print 'diff resampling = ', sum(DataBlock2_nosync-DataBlock2)
        DataBlock2_buff=np.append(DataBlock2_buff,DataBlock2)
        # Delay some data
        delay_DataBlock1 = Delay_Block1.process_data(DataBlock1)
        delay_DataBlock1_buf = np.append(delay_DataBlock1_buf,delay_DataBlock1)
        delay_DataBlock2 = Delay_Block2.process_data(DataBlock2)
        delay_DataBlock2_buf= np.append(delay_DataBlock2_buf,delay_DataBlock2)
        packetNr=packetNr+1

    # Calc: Coherence via Welch
    coherence1 = CW_Block1.process_data(DataBlock1_buff, DataBlock2_buff)
    # Calc: Coherence via Welch (delayed data)
    print 'diff1', sum(DataBlock1_buff-DataBlock2_buff)
    print 'diff2', sum(delay_DataBlock2_buf-delay_DataBlock1_buf)

    coherence2 = CW_Block2.process_data(delay_DataBlock1_buf, delay_DataBlock2_buf)
    print 'coh' ,sum(coherence2/coherence1)
    # Calc: Coherence Drift
    coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1, coherence2)
    # hand over to control block
    sro_info = ResamplingControl_Block.process_data(coherenceDrift)

    #  ---- Asncy Communication handling ----
    if sro_info['flag'] == True:
        Resampling_Block.process_async_data(sro_info['value'])

    print(sro_info['value'])
    n += 1024