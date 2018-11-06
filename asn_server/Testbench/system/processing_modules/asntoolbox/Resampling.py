import numpy as np


class Resampling:
    SamplingRateOffset = 0
    WindowSize = 20
    FrameSize = 0
    BlockType = "Resampling"
    BaseFrequency = 16000
    SampleCount = 0
    Ratio = 1

    # Constructor
    def __init__(self, params):
        self.SamplingRateOffset = params["SamplingRateOffset"]
        self.WindowSize = params["WindowSize"]
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        # hand trough

        # remember the amount of samples
        self.SampleCount += data.size
        return data

    # Asynchronous Processing of Data
    def process_async_data(self, data):
        self.SamplingRateOffset = data
        fsOffset = self.BaseFrequency * (1 + self.SamplingRateOffset / 1000000);
        self.Ratio = fsOffset / self.BaseFrequency;
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
