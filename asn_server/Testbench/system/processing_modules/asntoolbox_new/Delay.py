import numpy as np


class Delay:
    DelayInSamples = 0
    FrameSize = 0
    BlockType = "Delay"
    DataStore = np.zeros(1)
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.DelayInSamples = params["Delay"]
        self.FrameSize = params["FrameSize"]
        self.InstanceName = name
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        # first shift
        #for k in range(self.DelayInSamples):
        #    self.DataStore[k] = self.DataStore[k+self.FrameSize]
        self.DataStore[0:self.DelayInSamples] = self.DataStore[self.FrameSize:self.FrameSize+self.DelayInSamples]
        # second append new data
        #for k in range(self.FrameSize):
        #    self.DataStore[self.DelayInSamples+k] = data[k]
        self.DataStore[self.DelayInSamples:self.FrameSize+self.DelayInSamples] = data
        # copy data to output
        return self.DataStore[0:self.FrameSize]

    # Asynchronous Processing of Data
    def process_async_data(self):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.DataStore = np.zeros(self.DelayInSamples+self.FrameSize)
