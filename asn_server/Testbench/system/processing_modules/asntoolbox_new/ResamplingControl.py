import numpy as np


class ResamplingControl:
    BlockType = "ResamplingControl"
    UpdateAfterNumObservations = 100
    SmoothFactor = 0.95
    ObsCount = 0
    Sro = 0
    ControlValue = 0
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.SmoothFactor = params["SmoothFactor"]
        self.UpdateAfterNumObservations = params["UpdateAfterNumObservations"]
        self.InstanceName = name
        self.reset()
        # Process Params

    # DES Processing of Data
    def process_data(self, data):
        assert isinstance(data, (np.ndarray, np.generic))
        self.ObsCount += 1
        self.Sro = self.SmoothFactor * self.Sro + (1 - self.SmoothFactor) * (data+self.ControlValue)
        # self.Sro += data/(self.UpdateAfterNumObservations+1)

        if self.ObsCount > self.UpdateAfterNumObservations:
            self.ObsCount = 0
            # the new resampling factor as a combination of previous resampling factor and actual sro estimate
            # self.ControlValue = self.ControlValue + self.Sro
            print("SRO Estimate :",self.Sro, " Control Value ",self.ControlValue)
            self.ControlValue = self.Sro
            # reset actual sro
            # self.Sro = 0
            flag = True
        else:
            flag = False

        if self.ControlValue>=0:
            return {'value1':self.ControlValue, 'value2': 0, 'flag1':flag, 'flag2':flag}
        else:
            return {'value1': 0, 'value2': -self.ControlValue, 'flag1': flag, 'flag2':flag}

    # Asynchronous Processing of Data
    def process_async_data(self, params):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.Sro = 0
        self.ObsCount = 0
