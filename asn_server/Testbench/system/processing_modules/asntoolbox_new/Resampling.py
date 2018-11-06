import numpy as np


class Resampling:
    BaseFrequency = 16000
    WindowSize = 50
    SamplingRateOffset = 0
    Delay = 0
    Ratio = (1 + SamplingRateOffset / 1000000)
    SamplesInMem = WindowSize;
    WarmUpFlag = False;
    DropAfter = 10;
    FrameSize = 40960;
    SampleMemory = np.zeros(1)
    DriftInCrease = Ratio - 1
    DriftMemOffset = 0
    BlockType = "Resampling"
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.SamplingRateOffset = params["SamplingRateOffset"]
        self.WindowSize = params["WindowSize"]
        self.FrameSize = params["FrameSize"]
        self.InstanceName = name
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        # write data to mem
        for k in range(self.FrameSize):
            self.SampleMemory[self.SamplesInMem + k] = data[k]

        self.SamplesInMem = self.SamplesInMem + self.FrameSize;

        dataout = np.zeros(self.FrameSize)

        if (self.SamplesInMem < 2 * self.WindowSize + self.FrameSize):
            self.WarmUpFlag = True;
        else:
            self.WarmUpFlag = False;

        if (self.WarmUpFlag == False):
            for k in range(data.size):
                midval = np.round(self.DriftMemOffset) + k + self.WindowSize - 2
                StartIndex = midval - self.WindowSize
                if (StartIndex < 0):
                    StartIndex = 0

                EndIndex = midval + self.WindowSize
                if EndIndex >= 2 * self.WindowSize + self.FrameSize:
                    EndIndex = 2 * self.WindowSize + self.FrameSize

                tempsum = 0
                for m in range(int(StartIndex),int(EndIndex)):
                    ft = np.pi * (self.DriftMemOffset + k - m + self.WindowSize - self.Delay + 1)
                    if np.abs(ft)<= 0.001:
                        sincval = 1
                    else:
                        sincval = np.sin(ft)/ft
                    tempsum += self.SampleMemory[m] *  sincval

                dataout[k] = tempsum
                self.DriftMemOffset += self.DriftInCrease

            # Mem shift
            for k in range(self.SamplesInMem - self.FrameSize):
                self.SampleMemory[k] = self.SampleMemory[k+self.FrameSize]

            self.SamplesInMem -= self.FrameSize

            if self.DriftMemOffset > self.DropAfter:
                for k in range(self.SamplesInMem - self.DropAfter):
                    self.SampleMemory[k] = self.SampleMemory[k + self.DropAfter]

                self.SamplesInMem -= self.DropAfter
                self.DriftMemOffset -= self.DropAfter

        if self.WarmUpFlag == True:
            return {'value':dataout, 'flag': False}
        else:
            return {'value': dataout, 'flag': True}

    # Asynchronous Processing of Data
    def process_async_data(self, data):
        self.SamplingRateOffset = data
        self.Ratio = (1 + self.SamplingRateOffset / 1000000);
        self.DriftInCrease = self.Ratio - 1
        print("Process Async " + self.BlockType)

    def reset(self):
        self.SampleMemory = np.zeros(2 * self.WindowSize + 3 * self.FrameSize)
        self.Ratio = (1 + self.SamplingRateOffset / 1000000)
        self.SamplesInMem = self.WindowSize;
        self.DriftInCrease = self.Ratio - 1
        print("Reset " + self.BlockType)

