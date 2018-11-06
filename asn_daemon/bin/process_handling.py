import os, subprocess, signal

from subprocess import check_output
from bin.log_and_data import log

#---------------------------------------------------------
#class: process_c
#arguments:
#  - src: array of input pipes
#  - tar: array of output pipes
#  - path: path to the executable .py file
#  - name: name of the executable .py file
#  - para: array of parameters to start the process with
#---------------------------------------------------------
class process_c:
    def __init__(self,src,tar,path,name,para):
        self.sources = src
        self.targets = tar
        self.path = path
        self.name = name
        self.parameter = para
        self.stout = 0
        self.sterr = 0


#---------------------------------------------------------
#function: get_pid
#arguments:
#  - process: process whose PID is asked for
#return values:
#  - PID: PID of the given process
#---------------------------------------------------------
def get_pid(process):
    return map(int,check_output(["pidof",p]).split())


#---------------------------------------------------------
#function: execute_process
#arguments:
#  - process: process to start
#return values:
#  - subprocess: started subprocesses
#---------------------------------------------------------
def execute_process(process):
    try:
        gesamt = process.name
        for so in process.sources:
            gesamt = gesamt + " -i " + so
        for ta in process.targets:
            gesamt = gesamt + " -o " + ta
        gesamt = gesamt + " " + process.parameter
        errpipe = open(process.sterr,'w')  #TODO: open directly with fd
        outpipe = open(process.stout,'w')
        errfd = errpipe.fileno()
        outfd = outpipe.fileno()
        #print( 'will attempt to run', gesamt)
        return subprocess.Popen(gesamt, shell=True, preexec_fn=os.setsid, stderr=errfd, stdout=outfd, cwd=process.path)
        #print('Done subprocess!')

    except Exception as e:
        log("procces could not be started")
        log(type(e))
        log(e)


#---------------------------------------------------------
#function: execute_processes
#arguments:
#  - processes: array of processes to start
#return values:
#  - subprocesses: array of running subprocesses
#---------------------------------------------------------
def execute_processes(processes):
    subprocesses = []
    for pro in processes:
        subprocesses.append(execute_process(pro))
    return subprocesses


#---------------------------------------------------------
#function: kill_subprocesses
#arguments:
#  - subprocesses: array of subprocesses to kill
#  - handler: PID of the message handler
#return values:
#  - subprocesses: 0, list of subprocesses is empty
#  - handler: 0, handler not running
#  - running: 0, no subprocesses running in the background
#---------------------------------------------------------
def kill_subprocesses(subprocesses,handler):
    #check if any subprocesses were started
    if subprocesses == 0:
        return 0,0,0
    #kill all subprocesses
    for sub in subprocesses:
        try:
            os.killpg(os.getpgid(sub.pid), signal.SIGKILL)
        except Exception as e:
            log("subprocess could not be killed")
            log(type(e))
            log(e)
    #kill message handler if it was started
    if handler != 0:
        os.kill(handler, signal.SIGKILL)
    
    log("*Killed subprocesses")

    return 0,0,0


def terminate_subprocesses(subprocesses, handler):
    # check if any subprocesses were started
    if subprocesses == 0:
        return 0, 0, 0
    # kill all subprocesses

    for sub in subprocesses:
        try:
            #log("will terminate")
            #log(sub.pid+1)
            os.kill(sub.pid+1, signal.SIGTERM)
            #pgid = os.getpgid(sub.pid)
            #os.killpg(pgid, signal.SIGTERM)
        except Exception as e:
            log("subprocess could not be Terminated")
            log(type(e))
            log(e)
    # kill message handler if it was started
    # if handler != 0:
    #     log("will terminate hadnler first")
    #     log(handler)
    #     os.kill(handler, signal.SIGTERM)

    log("Terminated subprocesses")

    return 0, 0, 0