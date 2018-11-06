import numpy as np


class ResamplingControl:
    BlockType = "ResamplingControl"
    UpdateAfterNumObservations = 30
    SmoothFactor = 0.99
    ObsCount = 0
    Sro = 0

    # Constructor
    def __init__(self, params):
        self.SmoothFactor = params["SmoothFactor"]
        self.UpdateAfterNumObservations = params["UpdateAfterNumObservations"]
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        self.ObsCount += 1
        if self.ObsCount > self.UpdateAfterNumObservations:
            self.ObsCount = 0
            flag = True
        else:
            flag = False

        self.Sro = self.SmoothFactor * self.Sro + (1 - self.SmoothFactor) * data

        return {'value':self.Sro, 'flag':flag}

    # Asynchronous Processing of Data
    def process_async_data(self, params):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.Sro = 0
        self.ObsCount = 0
