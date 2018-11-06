from __future__ import print_function
import os, sys, socket, select, struct

from bin.socket_msg import socket_receive_msg

if __name__=="__main__":
    sockets = []
    listOfIds = sys.argv[1:]

    for id in listOfIds:
        # connect to pi
        try:
          int(id)
          ip =  str(id)
        except:
           ip = id

        try:
            soc1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc1.connect((ip, 9998))
            sockets.append(soc1)
            print("Connected to msg of "+str(ip))
        except:
            print("Unable to connect to msg of "+str(ip))
    
    while(1):
        try:
            readySockets = select.select(sockets,[],[])[0]
            for soc in readySockets:
                text = socket_receive_msg(soc)
                if text != "" and text != None:
                    print(text,end="")
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
