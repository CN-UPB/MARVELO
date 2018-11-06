import numpy as np


class CoherenceDriftEstimator:
    CoherenceTimeDelay = 1024
    FFTSize = 8192
    MaximumSRO = 300
    WelchShift = 1024
    BlockType = "CoherenceDriftEstimator"
    MaxFreqBin = np.rint(FFTSize/8);
    FreqBin = np.arange(FFTSize)
    FreqBinSum = 1
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.CoherenceTimeDelay = params["CoherenceTimeDelay"]
        self.FFTSize = params["FFTSize"]
        self.MaximumSRO = params["MaximumSRO"]
        self.WelchShift = params["WelchShift"]
        self.InstanceName = name
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data1, data2):
        assert isinstance(data1, (np.ndarray, np.generic))
        assert isinstance(data2, (np.ndarray, np.generic))
        drift = 0
        prod = data1 * np.conj(data2)
        angle = np.arctan2(np.imag(prod), np.real(prod)) / (2 * np.pi * self.CoherenceTimeDelay) * self.FFTSize
        prod = angle[1:int(self.MaxFreqBin)] * self.FreqBin[1: int(self.MaxFreqBin)]

        drift = -np.sum(prod) / self.FreqBinSum

        driftarray = np.ndarray(1)
        driftarray[0] = drift * 10**6
        return {'value':driftarray, 'flag':True}

    # Asynchronous Processing of Data
    def process_async_data(self):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.FreqBin = np.arange(self.FFTSize)
        val = np.rint(self.FFTSize / (4 * self.WelchShift * self.MaximumSRO * 10**(-6)))
        if val < self.MaxFreqBin:
            self.MaxFreqBin = val
        self.FreqBinSum = np.sum(self.FreqBin[2: int(self.MaxFreqBin)]**2)

