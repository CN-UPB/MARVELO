#!/usr/bin/env python
import os,sys
import argparse
import numpy as np
import scipy.io.wavfile
from scipy.io import wavfile
from scipy import linalg as LA
from multiprocessing import Queue,Process,Manager

q1= Queue()
q2= Queue()
pcount2=0
pcount1=0
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

def func1(q1,q2,inputs):
   sampleRate, data1 = scipy.io.wavfile.read('mix1.wav')
   sampleRate, data2 = scipy.io.wavfile.read('mix2.wav')
   for ccount in range(3):
    signal2 = list(np.fromfile(inputs[1], dtype=np.uint8, count=8192*2))#list(data1[ccount*4096:(ccount+1)*4096])#
    signal1 = list(np.fromfile(inputs[0], dtype=np.uint8, count=8192*2))#list(data2[ccount*4096:(ccount+1)*4096])#
    q1.put(signal1)#= np.array(list(signal1))
    q2.put(signal2)#audio2= signal2
    print 'read *',ccount
    sys.stdout.flush()

def func2(q1,q2,final1,final2):
  pcount1=0
  pcount2=0
  print 'func2: starting'
  audio1 = list()
  audio2 = list()
  while (pcount1+pcount2)<6 :#or pcount2<13:
    #print 'checking q'
    if audio2 and audio1:
        audio1 = []
        audio2 = []
    #while True:
    if not q1.empty() and not audio1:
            audio1[:] = q1.get()
            pcount1 = pcount1 + 1
            print 'caught pkt1*', pcount1


    #while True:
    if (not q2.empty()) and (not audio2):
            audio2[:] = q2.get()
            pcount2 = pcount2 + 1
            print 'caught pkt2*', pcount2



    sys.stdout.flush()
    #print '****checking length ******************', len(audio1)  , len(audio2)
    sys.stdout.flush()

    if len(audio1)>0  and len(audio2)>0:
        print 'processing pkt',pcount2,' len*', len(audio1),len(audio2)
        sys.stdout.flush()


        audio1 = np.array(audio1) / 255.0 - 0.5  # uint8 takes values from 0 to 255
        audio2 = np.array(audio2) / 255.0 - 0.5  # uint8 takes values from 0 to 255
        #wavfile.write('/home/pi/rx1.wav', Samplingrate, audio1)
        #wavfile.write('/home/pi/rx2.wav', Samplingrate, audio2)
        for pipe in inputs:
          pipe.close()
        x = [audio1, audio2]


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
        final1[:] = final1+list(Source[0])
        final2[:] = final2+list(Source[1])
        audio1=[]
        audio2=[]
        #final1[:] = final1+audio1#Source[0]
        #final2[:] = final2+audio2#Source[1]
  print 'func2: finishing'


#for pcount in range(13):




    # print 'Data len1', len(audio1)
    # print 'Data len2', len(audio2)
    # audio1 = audio1 / 255.0 - 0.5  # uint8 takes values from 0 to 255
    # audio2 = audio2 / 255.0 - 0.5  # uint8 takes values from 0 to 255
    # #wavfile.write('/home/pi/rx1.wav', Samplingrate, audio1)
    # #wavfile.write('/home/pi/rx2.wav', Samplingrate, audio2)
    # for pipe in inputs:
    #   pipe.close()
    # x = [audio1, audio2]
    #
    #
    # # Calculate The Covariance Matrix Of The Initial Data.
    # Cov = np.cov(x)
    # # Calculate Eigenvalues And Eigenvectors Of The Covariance Matrix.
    # D, E = LA.eigh(Cov)
    # # Generate A Diagonal Matrix With The Eigenvalues As Diagonal Elements.
    # D = np.diag(D)
    #
    # Di = LA.sqrtm(LA.inv(D))
    # # Perform Whitening. Xn Is The Whitened Matrix.
    # Xn = np.dot(Di, np.dot(np.transpose(E), x))
    #
    # # Perform Fobi.
    # Norm_Xn = LA.norm(Xn, axis=0)
    # Norm = [Norm_Xn, Norm_Xn]
    #
    # Cov2 = np.cov(np.multiply(Norm, Xn))
    #
    # D_N, Y = LA.eigh(Cov2)
    #
    # Source = np.dot(np.transpose(Y), Xn)
    # final1 = np.append(final1,Source[0])
    # final2 = np.append(final2,Source[1])
    #
#    final2 = np.append(final2,audio2)

with Manager() as manager:
    ff1 = manager.list()
    ff2 = manager.list()

    p1 = Process(target=func1,args=(q1,q2,inputs))
    p1.start()
    p2 = Process(target=func2,args=(q1,q2,ff1,ff2))
    p2.start()
    p1.join()
    p2.join()
    print 'ended'
    sys.stdout.flush()

    #sampleRate, data = scipy.io.wavfile.read('mix1.wav')
    print len(ff1)
#    print sum()
    wavfile.write('/home/asn/asn_daemon/logfiles/Estimated11.wav', Samplingrate, np.array(ff1))
    wavfile.write('/home/asn/asn_daemon/logfiles/Estimated22.wav', Samplingrate, np.array(ff2))
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

