import os, socket, subprocess

from lxml import etree, objectify
from bin.socket_msg import socket_send_msg, socket_receive_msg
from bin.process_handling import process_c
from bin.log_and_data import log

#---------------------------------------------------------
#class: NCcon_c
#arguments:
#  - i: target ip of the netcat connection
#  - po: target port of the netcat connection
#  - pi: pipe to use the netcat connection with
#---------------------------------------------------------
class NCcon_c:
    def __init__(self,i,po,pi):
        self.ip = i
        self.port = po
        self.pipe = pi

#---------------------------------------------------------
#function: listen_NC
#arguments:
#  - NCcon: NCcon_c object to start
#return values:
#  - subprocess: subprocess of the opened netcat connection
#---------------------------------------------------------
def listen_NC(NCcon):
    try:
        gesamt = str(NCcon.port) + " " + NCcon.pipe
        return subprocess.Popen(["python bin/netcatLis.py "+gesamt], shell = True, preexec_fn=os.setsid)
    except Exception as e:
        log("netcatLis.py could not be started")
        log(type(e))
        log(e)

#---------------------------------------------------------
#function: connect_NC
#arguments:
#  - NCcon: NCcon_c object to start
#return values:
#  - subprocess: subprocess of the opened netcat connection
#---------------------------------------------------------
def connect_NC(NCcon):
    try:
        gesamt = NCcon.ip + " " + str(NCcon.port) + " " + NCcon.pipe
        return subprocess.Popen(["python bin/netcatCon.py "+gesamt], shell = True, preexec_fn=os.setsid)
    except Exception as e:
        log("netcatCon.py could not be started")
        log(type(e))
        log(e)

#---------------------------------------------------------
#function: init_ingoing_connections
#arguments:
#  - connections: array of connections to open
#return values:
#  - subprocesses: array of subprocesses of opened netcat connections
#---------------------------------------------------------
def init_ingoing_connections(connections):
    subprocesses = []
    for con in connections:
        subprocesses.append(listen_NC(con))
    return subprocesses


#---------------------------------------------------------
#function: init_outgoing_connections
#arguments:
#  - connections: array of connections to open
#return values:
#  - subprocesses: array of subprocesses of opened netcat connections
#---------------------------------------------------------
def init_outgoing_connections(connections):
    subprocesses = []
    for con in connections:
        subprocesses.append(connect_NC(con))
    return subprocesses


#---------------------------------------------------------
#function: get_server_connection
#arguments:
#  - ip: ip of the server to connect to
#  - port: port of the server to connect to
#return values:
#  - server_socket: connected socket to the server
#---------------------------------------------------------
def get_server_connection(ip,port):
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    soc.bind((ip,port))
    soc.listen(5)
    server_socket, addr = soc.accept()
    return server_socket


#---------------------------------------------------------
#function: reconnect
#arguments:
#  - ip: ip of the server to connect to
#return values:
#  - server_cmd: connected command socket
#  - server_msg: connected message socket
#---------------------------------------------------------
def reconnect(ip):
    log("Waiting for server")
    try:
        server_cmd = get_server_connection(ip,9999)
        log("Command port connected")

        server_msg = get_server_connection(ip,9998)
        log("Message port connected")
    except Exception as e:
        log("Connection to server failed")
        log(type(e))
        log(e)

    return server_cmd,server_msg


#---------------------------------------------------------
#function: get_objects
#arguments:
#  - server_socket: socket, connected to the server
#return values:
#  - processes: array of processes to open
#  - connections_in: array of ingoing connections to open
#  - connections_out: array of outgoing connections to open
#---------------------------------------------------------
def get_objects(server_socket):
    processes = []
    connections_in = []
    connections_out = []
    dir_iterator = 1
    pipe_path = "/home/asn/asn_daemon/temp/pipes_system/fifo_"

    #send 'ack' to server to begin with transfer
    socket_send_msg(server_socket, "CMD ack")
    #receive data
    try:
        rootString = socket_receive_msg(server_socket)
    except Exception as e:
        log("Receiving data from server failed")
        log(type(e))
        log(e)

    #parse data
    root = objectify.fromstring(rootString)
    #get Pi-id
    pi_id = root.get("pi_id")

    #loop through executables
    for p in root.getchildren():
        input = []
        output = []
        parameter = ''
        #get name of executable
        name = p.get('executable') 
        #get path
        slash = name.rfind('/')
        path = 'system/'+str(dir_iterator)
        if slash != -1:
            path = path + '/' + name[:slash]
        dir_iterator = dir_iterator + 1

        #loop through parameters (input/output pipes and additional params)
        for atom in p.getchildren():
            
            # collect input pipes
            if(atom.tag == 'input'):
                pipe_id = atom.get("pipe_id")
                pipe_name = pipe_path+str(pipe_id)
                input.append(pipe_name)

                #register ingoing nc connection if necessary
                if atom.get("source_pi_id") != pi_id:
                  try:
                    int(pi_id)  
                    connections_in.append(NCcon_c("10.1.1."+str(pi_id),(1000+int(pipe_id)),pipe_name))
                  except Exception: 
                    connections_in.append(NCcon_c(str(pi_id),(1000+int(pipe_id)),pipe_name))

            # collect output fifos
            if(atom.tag == 'output'):
                pipe_id = atom.get("pipe_id")
                pipe_name = pipe_path+str(pipe_id)
                output.append(pipe_name)

                #register outgoing nc connection if necessary
                target_id = atom.get("target_pi_id")
                if target_id != pi_id:
                  try:
                    int(target_id)
                    connections_out.append(NCcon_c("10.1.1."+target_id, (1000+int(pipe_id)),pipe_name))
                  except Exception:
                    connections_out.append(NCcon_c(target_id, (1000+int(pipe_id)),pipe_name))
            # collect parameter
            if(atom.tag == 'parameter'):
                param = atom.get("param")
                parameter = parameter + param + " "

        # append new process
        processes.append(process_c(input,output,path,name,parameter))

    return processes, connections_in, connections_out
