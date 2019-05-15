#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy.io import wavfile
from scipy import linalg as LA


print "all modules"
def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")

    parser.add_argument("--param1","-p1",
                            type=int,
                            default=8192)
    parser.add_argument("--logfiles", "-l",
                            action="append")


    return parser.parse_args()
args = parse_arguments()
Samplingrate = 8000
print "all modules"


print "from allmodules: ", args.inputs
inputs = [os.fdopen(int(f), 'rb')for f in args.inputs]
#frame = np.fromfile(inputs[0], dtype='i2', count=50000)
#frame= inputs[0].readline()
#print frame
audio1= np.array([])
audio2= np.array([])
for pcount in range(13):
    signal1 = np.fromfile(inputs[0], dtype=np.uint8, count=4096)
    signal2 = np.fromfile(inputs[1], dtype=np.uint8, count=4096)
    audio1= np.append(audio1,signal1)
    audio2= np.append(audio2,signal2)




print 'Data len1', len(audio1)
print 'Data len2', len(audio2)
audio1 = audio1 / 255.0 - 0.5  # uint8 takes values from 0 to 255
audio2 = audio2 / 255.0 - 0.5  # uint8 takes values from 0 to 255
#wavfile.write('/home/pi/rx1.wav', Samplingrate, audio1)
#wavfile.write('/home/pi/rx2.wav', Samplingrate, audio2)
for pipe in inputs:
  pipe.close()
x = [audio1[0:50000], audio2[0:50000]]


# Calculate The Covariance Matrix Of The Initial Data.
Cov = np.cov(x)
# Calculate Eigenvalues And Eigenvectors Of The Covariance Matrix.
D, E = LA.eigh(Cov)
# Generate A Diagonal Matrix With The Eigenvalues As Diagonal Elements.
D = np.diag(D)

Di = LA.sqrtm(LA.inv(D))
# Perform Whitening. Xn Is The Whitened Matrix.
Xn = np.dot(Di, np.dot(np.transpose(E), x))

# Perform Fobi.
Norm_Xn = LA.norm(Xn, axis=0)
Norm = [Norm_Xn, Norm_Xn]

Cov2 = np.cov(np.multiply(Norm, Xn))

D_N, Y = LA.eigh(Cov2)

Source = np.dot(np.transpose(Y), Xn)


wavfile.write('/home/asn/asn_daemon/logfiles/Estimated11.wav', Samplingrate, Source[0])
wavfile.write('/home/asn/asn_daemon/logfiles/Estimated22.wav', Samplingrate, Source[1])
print 'finished processing'

'''

#Outputs = [Os.Fdopen(Int(F), 'Wb') For F In Args.Outputs]
#For Pipe In Outputs:
#        Pipe.Write(Dataresult)
#        Pipe.Flush()
#
#Logfiles = [Open(F, 'W') For F In Args.Logfiles]
#
#For File In Logfiles:
#            File.Write(Dataresult + '\N')
#            File.Flush()
#
#For File In Logfiles:
#    File.Close()
#	
#For Pipe In Outputs:
#    pipe.close()'''

