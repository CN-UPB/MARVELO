#!/usr/bin/env python

import os,sys
import argparse
import scipy.io.wavfile
import numpy as np
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--file", "-f",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--channel",
                            type=int,
                            default=1)

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
#timefile = open("/home/pi/asn_daemon/logfiles/readfile.log","w")
#print 'number of packets = ', dataLength/1024
#timefile.write('\n number of packets = '+ str(dataLength/1024))
#timefile.flush()
print 'start time: ', time.time()
sys.stdout.flush()

while dataPos < dataLength - ((PACKETSIZE/2)/dataChannels): #sample size is 2 bytes!
    #timefile.write('\nattemptToSend'+ str((dataPos/1024)))
    #timefile.flush()
    ch1 = data[dataPos:dataPos+int((PACKETSIZE/2)/dataChannels), :]
    #timefile.write('\nselect pkt'+ str((dataPos/1024)))
    #timefile.flush()
    #ch1= ch1.copy(order = 'C')
    #data_2_channels = np.reshape(ch1,(-1,2))
    #print 'will separate channels'
    sys.stdout.flush()

    #channel_1 = ch1[:,0].copy(order = 'C')
    #timefile.write('\nselect pkt - ch1'+ str((dataPos/1024)))
    #timefile.flush()
    channel_2 = ch1[:,args.channel].copy(order = 'C')
    #print 'diff at read ', sum(channel_1-channel_2)
    #timefile.write('\nselect pkt - ch2'+ str((dataPos/1024)))
    #timefile.flush()
    #pipes[1].write(channel_1)
    #pipes[1].flush()
    #timefile.write('\nwrote - ch2'+ str((dataPos/1024)))
    #timefile.flush()
    pipes[0].write(channel_2)
    pipes[0].flush()
    #timefile.write('\nwrote - ch2'+ str((dataPos/1024)))
    #timefile.flush()
    #print 'read some data'
    #timefile.write('\nread some data of size'+ str(len(channel_1)))
    #timefile.flush()

    #pipes[1].write(data[dataPos:dataPos+((PACKETSIZE/2)/dataChannels)-1, 1])ras
    #pipes[0].flush()
    #pipes[1].flush()
    #print len(ch1)
    #print ch1.size
    dataPos += int((PACKETSIZE/2)/dataChannels)
    #print 'sent packet',dataPos/1024
    sys.stdout.flush()

    #timefile.write('\nsendPkt'+ str((dataPos/1024)))
    #timefile.flush()


#close pipes
#timefile.close()
print("data transfer complete - exiting")
sys.stdout.flush()
for pipe in pipes:
    pipe.close()
