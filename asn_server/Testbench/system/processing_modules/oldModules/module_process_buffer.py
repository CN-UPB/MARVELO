import os,sys
import argparse
import numpy as np
import scipy.io.wavfile

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--input", "-i",
                            default="")
    parser.add_argument("--outputs", "-o",
                            action="append")

    return parser.parse_args()

args = parse_arguments()
PACKETSIZE = 4096 #receive data in 4KB packets (2KB or 1024 samples per channel equals shift amount used in processing blocks!)

#open input pipe
input = os.fdopen(int(args.input), 'rb')
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]

packetCount = 1
blockCount = 0

print("ready for first data")
sys.stdout.flush()
#assembling first 160KB (40960 samples) data block
frame = np.fromfile(input, dtype='i2', count=PACKETSIZE/2) #item size is 2 bytes
while packetCount <  40:
    packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2)
    frame = np.append(frame, packet)
    packetCount += 1
print("first block of 40960 samples received")
sys.stdout.flush()
print("start sending data from buffer (1024 samples offset")
sys.stdout.flush()
#loop while data is still coming in -> last packet is skipped because it is not complete
while packet.size == PACKETSIZE/2:

    #shift frame 2048 items forward (4096 bytes - 1024 samples/channel) using next packet
    if blockCount != 0:
        frame = frame[2048:]
        frame = np.append(frame, packet)

    #make copy of frame (in case processing changes this data)
    DataBlock = frame.copy()

    #reshape frame to prepare channel seperation
    DataBlock = np.reshape(DataBlock, (40960, 2))

    #seperate channels for processing
    DataBlock1 = DataBlock[:, 1]
    DataBlock2 = DataBlock[:, 0]

    #write channels to seperate outputs
    outputs[0].write(DataBlock1.tobytes()) #must be written as c contiguous bytestream (left/right channel are interleaved)
    outputs[0].flush()

    outputs[1].write(DataBlock2.tobytes())
    outputs[1].flush()

    #read next packet from input
    packet = np.fromfile(input, dtype='i2', count=PACKETSIZE/2)

    packetCount += 1
    blockCount += 1

print("no more data - exiting")
sys.stdout.flush()
#close pipes
input.close()
for pipe in outputs:
    pipe.close()
