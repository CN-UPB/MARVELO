#!/usr/bin/env python

import os,sys
import argparse
import scipy.io.wavfile

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
#print "output pipes " , args.outputs
PACKETSIZE = 4096 #send data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)

#read complete file using scipy
print("begin reading audio file")
sys.stdout.flush()
sampleRate, data = scipy.io.wavfile.read(args.file)
#sampleRate, data = scipy.io.wavfile.read('/home/hafifi/Desktop/docPaderborn/asnRepo/p1/Testbench/asn_server_Emulator/asn_server/Testbench/system/readfile_module/AudioData/Audio_2Chan_80ppm.wav')

data = data.copy(order ='C')
dataLength, dataChannels = data.shape
sampleSize = data.itemsize
dataSize = dataLength * dataChannels * sampleSize

#print some information about the file
print("file read successfully:\n -sampleRate = %d samples/sec\n -sampleSize = %d bytes\n -bitrate per channel = %d kb/s\n -\
dataLength = %d samples\n -dataChannels = %d channels\n -dataSize = %d KiB\n -duration = %f sec"\
%(sampleRate, sampleSize, sampleRate*sampleSize*8/1000, dataLength, dataChannels, dataSize/1024, dataLength/sampleRate))
sys.stdout.flush()

#open pipes
pipes = [os.fdopen(int(f), 'wb') for f in args.outputs]

#write file to pipes
print("writing data to output pipe in 4KB packets")
sys.stdout.flush()
dataPos = 0
while dataPos < dataLength - ((PACKETSIZE/2)/dataChannels): #sample size is 2 bytes!
    ch1 = data[dataPos:dataPos+((PACKETSIZE/2)/dataChannels), :]
    ch1= ch1.copy(order = 'C')
    pipes[0].write(ch1)
    #pipes[1].write(data[dataPos:dataPos+((PACKETSIZE/2)/dataChannels)-1, 1])
    #pipes[0].flush()
    #pipes[1].flush()
    #print len(ch1)
    #print ch1.size
    dataPos += ((PACKETSIZE/2)/dataChannels)

#close pipes
print("data transfer complete - exiting")
sys.stdout.flush()
# for pipe in pipes:
#     pipe.close()
