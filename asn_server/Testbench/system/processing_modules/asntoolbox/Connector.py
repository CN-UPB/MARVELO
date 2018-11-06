import numpy as np
from collections import deque


class Connector:
    FrameSize = 0
    BlockType = "Connector"
    FramesInMem = 0
    InstanceName = "unknown"

    # Constructor
    def __init__(self, name):
        self.InstanceName = name
        self.reset()

    def push_data(self, data):
        self.DataStore.append(data)
        self.FramesInMem += 1

    def pop_data(self):
        dataOut = self.DataStore.popleft()
        self.FramesInMem -= 1

        return dataOut

    def has_data(self):
        if self.FramesInMem > 0:
            return True
        else:
            return False

    def reset(self):
        print("Reset " + self.BlockType)
        self.DataStore = deque()
