

class Vad:
    AvgEnergy = 1.0
    EnergySmoothFactor = 0.9
    OvershootFactor = 2.0
    StartupFlag = True
    BlockType = "VAD"
    InstanceName = "unknown"

    # Constructor
    def __init__(self, params, name):
        self.reset()
        # Process Params
        self.EnergySmoothFactor = params["EnergySmoothFactor"]
        self.OvershootFactor = params["OvershootFactor"]
        self.InstanceName = name

    # DES Processing of Data
    def process_data(self, data):
        energy_in_block = 0.0
        vad = False
        for sample in data:
            energy_in_block += sample**2

        if self.StartupFlag:
            self.AvgEnergy = energy_in_block
            self.StartupFlag = False

        if self.OvershootFactor * self.AvgEnergy < energy_in_block:
            vad = True
        else:
            self.AvgEnergy = self.EnergySmoothFactor * self.AvgEnergy + (1 - self.EnergySmoothFactor) * self.AvgEnergy

        return vad

    # Asynchronous Processing of Data
    def process_async_data(self):
        print("Process Async " + self.BlockType)

    def reset(self):
        print("Reset " + self.BlockType)
        self.AvgEnergy = 1.0
        self.StartupFlag = True
