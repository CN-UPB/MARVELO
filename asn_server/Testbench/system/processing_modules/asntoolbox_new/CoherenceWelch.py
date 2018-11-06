import numpy as np


class CoherenceWelch:
    FFTSize = 8192
    WelchShift = 1024
    WindowType = "Hann"
    Window = np.ones(FFTSize)
    BlockType = "CoherenceWelch"
    InstanceName = "unknown"

    # Constructor
    def __init__(self, param, name):
        self.FFTSize = param["FFTSize"]
        self.WelchShift = param["WelchShift"]
        self.WindowType = param["WindowType"]
        self.InstanceName = name
        self.reset()

    # DES Processing of Data
    def process_data(self, data1, data2):
        assert isinstance(data1, (np.ndarray, np.generic))
        assert isinstance(data2, (np.ndarray, np.generic))

        autocorrelation1 = np.zeros(self.FFTSize, dtype=np.complex)
        autocorrelation2 = np.zeros(self.FFTSize, dtype=np.complex)
        crosscorrelation = np.zeros(self.FFTSize, dtype=np.complex)
        n = 0
        while n < data1.size - self.FFTSize:
            Prod1 = self.Window * data1[n:n + self.FFTSize]
            Prod2 = self.Window * data2[n:n + self.FFTSize]
            fft1 = np.fft.fft(Prod1)
            fft2 = np.fft.fft(Prod2)
            autocorrelation1 += fft1 * np.conj(fft1)
            autocorrelation2 += fft2 * np.conj(fft2)
            crosscorrelation += fft1 * np.conj(fft2)
            n += self.WelchShift
        # Coherence
        coherence = crosscorrelation/(np.sqrt(autocorrelation1) * np.sqrt(autocorrelation2) + 0.000001)
        return {'value':coherence, 'flag':True}

    # Asynchronous Processing of Data
    def process_async_data(self):
        print("Process Async")

    def reset(self):
        print("Reset "+self.BlockType)
        if self.WindowType == "Hann":
            self.Window = np.hanning(self.FFTSize)
        if self.WindowType == "Blackmann":
            self.Window = np.blackman(self.FFTSize)
        if self.WindowType == "Rect":
            self.Window = np.ones(self.FFTSize)
