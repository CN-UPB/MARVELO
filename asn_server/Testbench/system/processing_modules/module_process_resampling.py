#!/usr/bin/env python
import os,sys
import ast
import argparse
import numpy as np
import scipy.io.wavfile
from asntoolbox import Resampling
import time
import select
def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument("--inputs", "-i",
                            action="append")
    parser.add_argument("--outputs", "-o",
                            action="append")
    parser.add_argument("--logfiles", "-l",
                            action="append")
    parser.add_argument("--SamplingRateOffset",
                            type=int,
                            default=0)
    parser.add_argument("--WindowSize",
                            type=int,
                            default=20)

    return parser.parse_args()

args = parse_arguments()

#init processing block
resampling_params = {"SamplingRateOffset": args.SamplingRateOffset, "WindowSize": args.WindowSize}
Resampling_Block = Resampling(resampling_params)
# open time file
#timefile = open("/home/pi/asn_daemon/logfiles/resamplingFile.log","w")
# start timing 
start = time.time()
#open input pipes
inputs = ["null", "null"]
inputs[0] = os.fdopen(int(args.inputs[0]), 'rb')
inputs[1] = os.fdopen(int(args.inputs[1]), 'r') #not binary mode because dictionary is sent as string
#open output pipes
outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
#open log files
#logfiles = [open(f, 'w') for f in args.logfiles]
sro_info_string=""
print("ready for processing - entering loop")
sys.stdout.flush()
# counter = 0
Data = []
counterPkt = 0

while 1:
        #do async processing (loopback!)
        #timefile.write('will read in resampling\n')
        #timefile.flush() 
    #read data from pipe 1024
        while 1:
              #print "write in pipe sampling"
              #sys.stdout.flush()
              r, w, e = select.select([int(args.inputs[0])], [], [], 1024)
              if int(args.inputs[0]) in r:
                  Data = np.fromfile(inputs[0], dtype='i2',
                                   count=1024)  # data[n+packetNr*packetLen:(n+packetLen)+packetNr*packetLen, 1]
                  counterPkt += 1

                  break
              else:
                  pass
                  #print "nothing available from resampling 0!"  # or just ignore that case
                  #sys.stdout.flush()

                  #time.sleep(1)
          #Data = np.fromfile(inputs[0], dtype='i2', count=1024)
          #do processing
        #timefile.write('read some dara resampling\n')
        #timefile.flush()
        DataResult = Resampling_Block.process_data(Data)
        #timefile.write('processedresampling\n')
        #timefile.flush()
        #write output data to pipe(s)
        for pipe in outputs:
            pipe.write(DataResult)
            pipe.flush()
            #print "write in pipe sampling"
            #sys.stdout.flush()

        ## will read asynch
        # sro_info_string = inputs[1].readline() #read 2nd input
        # if sro_info_string:
        #     #timefile.write(sro_info_string+ 's\n')
        # #timefile.write(' read \n')
        # #timefile.flush()

        while 1:
             #timefile.write(' checking pipe \n')
             #timefile.flush()

             r, w, e = select.select([int(args.inputs[1])], [], [], 1)
             #timefile.write(' checked pipes \n')
             #timefile.flush()

             if int(args.inputs[1]) in r:
                  sro_info_string = inputs[1].readline()  # read 2nd input
                  #timefile.write(' read sro \n')
                  #timefile.flush()

                  #print(">>>>sro value: " + str(sro_info_string))
                  #sys.stdout.flush()
                  #print 'sro type ', sro_info_string
                  #sys.stdout.flush()

                  sro_info = ast.literal_eval(str(sro_info_string)) #convert string to dictionary
                  if sro_info['flag'] == True:
                      Resampling_Block.process_async_data(sro_info['value']) #processing

                      #print("sro value: " + str(sro_info_string))
                      #sys.stdout.flush()
                  # print timing
                  end = time.time()
                  timeElapsed = (end - start)
                  #print 'elapsed-->',timeElapsed
                  #sys.stdout.flush()

                  #timefile.write(str(timeElapsed)+ '\n')
                  #timefile.flush()
                  #write log data to file
                  #for file in logfiles:
                   #   file.write(str(sro_info['value']) + '\n')
                   #   file.flush()

                  break
             else:
                  #print "nothing available from pipe 1 resampling!",  # or just ignore that case
                  #sys.stdout.flush()
                  #timefile.write('nothing available from pipe 1 resampling!\n')
                  #timefile.flush()
                  if counterPkt<40:
                      break

        # print value for demonstration purposes
        #for file in logfiles:
        # file.write(sro_info_string + '\n')
        # file.flush()

end = time.time()
timeElapsed = (end - start)
print 'elapsed-->',timeElapsed
sys.stdout.flush()

##timefile.write(str(timeElapsed))
#timefile.flush()

#timefile.close()

#close pipes and files
for pipe in inputs:
    pipe.close()
for pipe in outputs:
    pipe.close()
#for file in logfiles:
#    file.close()
