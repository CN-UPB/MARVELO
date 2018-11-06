import numpy as np

class Reframe:
    InFrameSize = 0
    OutFrameSize = 0
    SampleInMem = 0
    BlockType = "Reframe"
    BufferFull = False
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.InFrameSize = params["InFrameSize"]
        self.FrameShift = params["FrameShift"]
        self.OutFrameSize = params["OutFrameSize"]
        self.InstanceName = name
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        # If last time the buffer emitted a paket, move renmaining values upfront
        if self.BufferFull:
            #for k in range(self.SampleInMem-self.FrameShift):
            #    self.DataStore[k] = self.DataStore[k+self.FrameShift]
            self.DataStore[0:self.SampleInMem-self.FrameShift] = self.DataStore[self.FrameShift:self.SampleInMem]
            self.SampleInMem -= self.FrameShift

        # append data
        #for k in range(self.InFrameSize):
        #    self.DataStore[k + self.SampleInMem] = data[k]
        self.DataStore[self.SampleInMem:self.SampleInMem+self.InFrameSize] = data

        self.SampleInMem += self.InFrameSize

        if self.SampleInMem >= self.OutFrameSize:
            self.BufferFull = True
        else:
            self.BufferFull = False

        # copy data to output
        return {'value': self.DataStore[0:self.OutFrameSize], 'flag': self.BufferFull}

    # Asynchronous Processing of Data
    def process_async_data(self):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.DataStore = np.zeros(2*self.InFrameSize+self.OutFrameSize)
        self.SampleInMem = 0
        self.BufferFull = False
