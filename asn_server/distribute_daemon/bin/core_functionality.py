import os, select

from bin.socket_msg import socket_send_msg, socket_receive_msg
from bin.connection import NCcon_c,listen_NC,connect_NC,init_outgoing_connections,init_ingoing_connections,get_server_connection,reconnect,get_objects
from bin.pipes import init_pipes,open_ingoing_pipes,open_outgoing_pipes
from bin.process_handling import process_c,execute_processes,kill_subprocesses
from bin.log_and_data import log

#---------------------------------------------------------
#function: start_handler
#arguments:
#  - server: message socket connected to the server
#  - processes: array of processes 
#  - id: own pi-id
#return values:
#  - new_pid: PID of the started handler
#  - processes: changed array of process objects with 
#    stderr and stdout filenames 
#---------------------------------------------------------
def start_handler(server,processes,id):
    iterator = 1
    pipes = []
    open_pipes = []
    
    #clear msg pipes for subprocesses
    os.system("rm -f -r temp/pipes_intern/*")
    #clear logfile directory, but keep daemon.log
    os.system("cd logfiles && ls * | grep -v daemon.log | xargs rm -rf")

    #create pipes for every subprocess in 
    for pro in processes:
        #create stderr pipe
        err_name = "temp/pipes_intern/err_"+pro.name.split('.')[0]+"_"+str(iterator)
        os.mkfifo(err_name)
        pipes.append(err_name)
        #create out pipe
        out_name = "temp/pipes_intern/out_"+pro.name.split('.')[0]+"_"+str(iterator)
        os.mkfifo(out_name)
        pipes.append(out_name)
        #give name of pipes to process
        pro.stout = out_name
        pro.sterr = err_name

        #create logfile for module
        log_name = "logfiles/"+pro.name.split('.')[0]+"_"+str(iterator)+".log"
        os.system("touch "+log_name)
        #increment iterator
        iterator = iterator+1

    #start handler as subprocess
    new_pid = os.fork()
    if new_pid == 0:
        open_pipes = [open(pipe,'r') for pipe in pipes]
        while True:
            ready_pipes = select.select(open_pipes,[],[])[0]
            for pipe in ready_pipes:
                #analyze information given by pipe
                pipe_name = pipe.name.split('/')[-1]
                pipe_name_splitted = pipe_name.split('_')
                msg_type = pipe_name_splitted[0]
                #rebuilding the module name even with '_' in the name
                module_name_list = pipe_name_splitted[1:-1]
                module_name = module_name_list[0]
                for name in module_name_list[1:]:
                    module_name = module_name + '_' + name
                iterator = pipe_name_splitted[-1]
                #read from pipe
                data = pipe.readline()
                if data != "" and data != " ":
                    #write to logfile
                    log_name = "logfiles/"+module_name+"_"+str(iterator)+".log"
                    file = open(log_name,'a')
                    file.write(data)
                    file.close()
                    #send to debug window of server
                    socket_send_msg(server,"Pi "+str(id)+", "+module_name+": "+data)
    return new_pid,processes
	

#---------------------------------------------------------
#function: start
#arguments:
#  - server_cmd: command socket connected to the server
#  - server_msg: message socket connected to the server
#  - id: own pi-id
#return values:
#  - subprocesses: array of started subprocesses
#  - running: 1 as status for running subprocesses
#  - handler: PID of the message handler subprocess
#---------------------------------------------------------
def start(server_cmd,server_msg,id):
    #no subprocesses running
    subprocesses = []
    
    #get objects from the server
    processes,connections_in,connections_out = get_objects(server_cmd)

    #initialize pipes
    init_pipes(processes)
    #initialize ingoing connections
    subprocesses = subprocesses + init_ingoing_connections(connections_in)
    #initialize outgoing connections
    subprocesses = subprocesses + init_outgoing_connections(connections_out)

    #open read pipes (non blocking!)
    processes = open_ingoing_pipes(processes)

    #start message handler
    handler,processes=start_handler(server_msg,processes,id)
    running = 1

    #wait for starting signal from server (synchronization)
    try:
        socket_send_msg(server_cmd,"ready")
        socket_receive_msg(server_cmd)
    except Exception as e:
        log("synchronization with server failed")
        log(type(e))
        log(e)

    #open write pipes
    processes = open_outgoing_pipes(processes)
    #run processes
    log("execute processes")
    subprocesses = subprocesses + execute_processes(processes)

    return subprocesses,running,handler
