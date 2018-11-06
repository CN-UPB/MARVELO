#!/usr/bin/env python
import os,sys
import argparse
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='arguments')


    parser.add_argument("--outputs", "-o",
                            action="append")
 
    return parser.parse_args()

args = parse_arguments()


### Open a file
##fdi = os.open( args.inputs[0], os.O_RDWR)
###fdo = os.open( ''.join([args.outputs[0],'.txt']), os.O_RDWR|os.O_CREAT )
##outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
##
### Now get a file object for the above file.
###fo = os.fdopen(fdo, "w+")
###fi = os.read(fdi,100)
##fip = os.fdopen(fdi, "rw+")
###fidata = np.fromfile(fip,dtype='int', count= -1)
##fidata = np.loadtxt(fip,dtype='i2')
###print ' read data = ',fidata
### Write in string file
###print 'data is ',fidata
##
###fo.write(fidata)
##np.savetxt(args.outputs[0],np.array([fidata]), fmt='%.4e')
### Write in pipef
##for pipe in outputs:
##        pipe.write(''.join([np.array_str(fidata),'\n']))
##        pipe.flush()
### Close opened file
###fo.close()

outputs = [os.fdopen(int(f), 'wb') for f in args.outputs]
inputSig = 10
for pipe in outputs:
        print "writing data"
        pipe.write("10\n")
        #pipe.flush()
        print "written"
for pipe in outputs:
    pipe.close()
print "Closed the file successfully!!"
