import os

from bin.process_handling import process_c
from bin.log_and_data import log

#---------------------------------------------------------
#function: init_pipes
#arguments:
#  - processes: array of all processes
#---------------------------------------------------------
def init_pipes(processes):
    #go through all processes
    for pro in processes:
        #go through all source pipes
        for pipe in pro.sources:
            #delete the pipe if it already exists
            if os.path.exists(pipe):
               os.remove(pipe)
            #create the pipe
            os.mkfifo(pipe)
        #go through all target pipes
        for pipe in pro.targets:
            #delete the pipe if it already exists
            if os.path.exists(pipe):
               os.remove(pipe)
            #create the pipe
            os.mkfifo(pipe)


#---------------------------------------------------------
#function: open_ingoing_pipes
#arguments:
#  - processes: array of all processes
#return values:
#  - processes_new: new array of processes with file
#    descriptors instead of source pipe paths
#---------------------------------------------------------
def open_ingoing_pipes(processes):
    #create array for the new processes
    processes_new = []
    #go through all processes
    for pro in processes:
        #create array of file descriptors
        openFD = []
        #go through all source pipes
        for pipe in pro.sources:
            #open pipe in RDWR mode to avoid blocking
            FD = os.open(pipe, os.O_RDWR)
            #collect opened fildescriptors in array
            openFD.append(str(FD))

        #append new process with file descriptors instead of pipe paths as parameters
        processes_new.append(process_c(openFD,pro.targets,pro.path,pro.name,pro.parameter))
    #return new array
    return processes_new


#---------------------------------------------------------
#function: open_outgoing_pipes
#arguments:
#  - processes: array of all processes
#return values:
#  - processes_new: new array of processes with file
#    descriptors instead of target pipe paths
#---------------------------------------------------------
def open_outgoing_pipes(processes):
    #create array for the new processes
    processes_new = []
    #go through all processes
    for pro in processes:
        #create array of file descriptors
        openFD = []
        #go through all target pipes
        for fifo in pro.targets:
            #open pipe in write mode
            FD = os.open(fifo, os.O_WRONLY)
            #collect opened fildescriptors in array 
            openFD.append(str(FD)) 

        #create new process with file descriptors instead of pipe paths as parameters
        new_proc = process_c(pro.sources,openFD,pro.path,pro.name,pro.parameter)
        new_proc.sterr = pro.sterr
        new_proc.stout = pro.stout
        #append new process
        processes_new.append(new_proc)
    #return new array
    return processes_new
