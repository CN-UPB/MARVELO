import os, socket
import time

from lxml import etree, objectify
from bin.xml_and_log import parse_xml
from bin.socket_msg import socket_send_msg, socket_receive_msg

#---------------------------------------------------------
#function: connect
#arguments:
#  - xmlfile: xml file to get the addresses from
#  - connected: status if connected or not
#  - sockets: array of existing command sockets or -1
#return values:
#  - cmd_sockets: array of command sockets
#  - connected: status if connected or not
#---------------------------------------------------------
def connect(xmlfile,connected,sockets):
    
    if xmlfile == "":
        print("Set xml-file before connecting")
        return -1,0
        
    if connected == 1:
        for soc in sockets:
            socket_send_msg(soc, "reconnect")
        time.sleep(1)
    
    root_as_string = parse_xml(xmlfile)
    root = objectify.fromstring(root_as_string)
    
    nodes = []
    cmd_sockets = []

    for element in root.getchildren():
        nodes.append(etree.tostring(element))
    
    # do for every pi
    for node in nodes:
        # connect to pi
        ip = ""
        try:
           int(objectify.fromstring(node).get("pi_id"))
           ip = "10.1.1." + objectify.fromstring(node).get("pi_id")
        except Exception:
           ip = objectify.fromstring(node).get("pi_id")
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.connect((ip, 9999))
            cmd_sockets.append(soc)
            print("Connected to cmd of "+str(ip))
        except Exception as e:
            print e
            print "Unable to connect to cmd of {}".format(ip)

    if len(cmd_sockets) < 1:
        return -1,0
    else:
        return cmd_sockets,1

#---------------------------------------------------------
#function: is_online
#arguments:
#  - sockets: array of existing command sockets or -1
#---------------------------------------------------------
def is_online(sockets):
    if sockets != -1:
        for soc in sockets:
            ip = soc.getpeername()
            socket_send_msg(soc, "isonline")
            socket_receive_msg(soc)
            print(str(ip) + " is connected")
    else:
        print("Sockets not connected yet")
