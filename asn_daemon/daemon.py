import os, sys, signal

import netifaces as ni

import argparse



from bin.socket_msg import socket_send_msg, socket_receive_msg

from bin.connection import get_server_connection,reconnect

from bin.log_and_data import create_log,log,delete_data

from bin.process_handling import kill_subprocesses, terminate_subprocesses

from bin.core_functionality import start,start_handler





#create global variable for logfile

logfile = 0



def parse_arguments():

    parser = argparse.ArgumentParser(description='arguments')

    parser.add_argument('--iface', "-if", action='append')

    return parser.parse_args()





if __name__ == "__main__":

    args = parse_arguments()

    try :
        iface = args.iface[0]
    except Exception :
        iface = 'wlan0'
    #if iface == "":
    #    iface = 'wlan0'

    #initialize logfile variable

    create_log("logfiles/daemon.log")

    

    #get own address and id

    ni.ifaddresses(iface)

    ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']

    id = ip.split(".")[-1]

    

    #create necessary variables

    cmdPort = 9999

    msgPort = 9998

    handler = 0

    subprocesses = 0

    running = 0

    

    #define handler for SIGTERM signal

    def sigterm_handler(signum, frame):

        terminate_subprocesses(subprocesses,handler)

        log("killed by SIGTERM")

        sys.exit(0)

    

    #set handler for SIGTERM signal

    signal.signal(signal.SIGTERM, sigterm_handler)



    #connect to server

    try:

        log("Waiting for server")

        server_cmd = get_server_connection(ip,cmdPort)

        log("Command port connected")

        server_msg = get_server_connection(ip,msgPort)

        log("Message port connected")

    except Exception as e:

        log("Connection to server failed")

        log(type(e))

        log(e)



    #main-loop, waiting for commands of server

    while(1):

        command = socket_receive_msg(server_cmd)

        if command == "start":

            try:

                subprocesses,running,handler = start(server_cmd,server_msg,id)

            except Exception as e:

                log("start method failed")

                log(type(e))

                log(e)

        elif command == "abort":

            try:

                subprocesses,handler,running = kill_subprocesses(subprocesses,handler)

            except Exception as e:

                log("killing of subprocces failed")

                log(type(e))

                log(e)
        elif command == "gentleAbort":

            try:

                subprocesses,handler,running = terminate_subprocesses(subprocesses,handler)

            except Exception as e:

                log("killing of subprocces failed")

                log(type(e))

                log(e)

        elif command == "delete":

            delete_data()

        elif command == "reconnect":

            try:

                server_cmd,server_msg = reconnect(ip)

            except Exception as e:

                log("reconnect method failed")

                log(type(e))

                log(e)

        elif command == "isonline":

            try:

                socket_send_msg(server_cmd, "online")

            except Exception as e:

                log("sending online status failed")

                log(type(e))

                log(e)