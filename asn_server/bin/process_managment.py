import os, socket

from lxml import etree, objectify
from bin.xml_and_log import parse_xml
from bin.socket_msg import socket_send_msg, socket_receive_msg

#---------------------------------------------------------
#function: abort
#arguments:
#  - sockets: array of sockets to send the abort message to
#---------------------------------------------------------
def abort(sockets):
    if sockets == -1:
        print("Sockets not connected yet")
        return
    for so in sockets:
        socket_send_msg(so, "abort")

def gentleAbort(sockets):
    if sockets == -1:
        print("Sockets not connected yet")
        return
    for so in sockets:
        socket_send_msg(so, "gentleAbort")

#---------------------------------------------------------
#function: start
#arguments:
#  - xmlfile: string with path and name of the xml file
#  - sockets: sockets connected to all partictipating pis
#---------------------------------------------------------
def start(xmlfile,sockets):
    if (xmlfile == "") or (sockets == -1):
        print("Set xml-file and connect before starting")
        return -1

    print("Start: "+xmlfile)
    
    root_as_string = parse_xml(xmlfile)
    root = objectify.fromstring(root_as_string)
    
    nodes = []
 
    for element in root.getchildren():
        nodes.append(etree.tostring(element))
    
    #do for every pi
    for node,soc in zip(nodes,sockets):
      try:
        int(objectify.fromstring(node).get("pi_id"))
        ip = "10.1.1." + objectify.fromstring(node).get("pi_id")
        #send 'start' command to pi and wait for 'ack'
        socket_send_msg(soc, "start")
        socket_receive_msg(soc)
        socket_send_msg(soc, node)
        socket_receive_msg(soc)
        print([ip + " is ready"])
      except Exception:          
        ip = objectify.fromstring(node).get("pi_id")
        #send 'start' command to pi and wait for 'ack'
        socket_send_msg(soc, "start")
        socket_receive_msg(soc)
        socket_send_msg(soc, node)
        socket_receive_msg(soc)
        print([ip + " is ready"])
        
    for soc in sockets:
        socket_send_msg(soc, "start")
    
    return
