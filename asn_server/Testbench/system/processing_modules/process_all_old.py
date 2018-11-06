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
delay_params = {"FrameSize": 40960, "Delay": 1024}
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
while n < dataLength - 5 * 8192:
    # Get Data
    DataBlock1 = data[n:n + 5 * 8192, 1]
    DataBlock2_nosync = data[n:n + 5 * 8192, 0]

    # ------ Sync Processing - DES ----------
    # Resampling of second stream
    DataBlock2 = Resampling_Block.process_data(DataBlock2_nosync)
    # Process VAD
    vad_value = Vad_Block.process_data(DataBlock1)
    # Calc: Coherence via Welch
    coherence1 = CW_Block1.process_data(DataBlock1, DataBlock2)
    # Delay some data
    delay_DataBlock1 = Delay_Block1.process_data(DataBlock1)
    delay_DataBlock2 = Delay_Block2.process_data(DataBlock2)
    # Calc: Coherence via Welch (delayed data)
    coherence2 = CW_Block2.process_data(delay_DataBlock1, delay_DataBlock2)
    # Calc: Coherence Drift
    coherenceDrift = CoherenceDriftEstimator_Block.process_data(coherence1, coherence2)
    # hand over to control block
    sro_info = ResamplingControl_Block.process_data(coherenceDrift)

    #  ---- Asncy Communication handling ----
    if sro_info['flag'] == True:
        Resampling_Block.process_async_data(sro_info['value'])

    print(sro_info['value'])
    n += 1024