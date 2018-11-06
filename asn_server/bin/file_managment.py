import os, socket
from bin.socket_msg import socket_send_msg
from bin.xml_and_log import parse_xml
from lxml import etree, objectify

#---------------------------------------------------------
#function: delete
#arguments:
#  - sockets: array of sockets to send the delete message to
#---------------------------------------------------------
def delete(sockets):
    if sockets == -1:
        print("Not connected")
        return
    for so in sockets:
        socket_send_msg(so, "delete")

#---------------------------------------------------------
#function: send_file
#arguments:
#  - node: node from the xml file
#  - ip: ip to send the files to
#---------------------------------------------------------
def send_file(node,ip):
    iterator = 1
    for module in node.getchildren():
        path = module.get("path")
        targetPath = "~/asn_daemon/system"
        os.system("mkdir -p "+str(iterator))
        os.system("cp -r " + path + "/* " + str(iterator))
        os.system("scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error -r " + str(iterator) + " asn@" + ip + ":" + targetPath)
        os.system("rm -r -f " + str(iterator))
        iterator = iterator + 1

#---------------------------------------------------------
#function: send_data
#arguments:
#  - xmlfile: xml file to read the data from
#  - sockets: sockets to send the data to
#---------------------------------------------------------
def send_data(xmlfile,sockets):
    if (xmlfile == "") or (sockets == -1):
        print("set xml-file and connect before starting")

    root_as_string = parse_xml(xmlfile)
    root = objectify.fromstring(root_as_string)
    
    nodes = []
    
    for element in root.getchildren():
        nodes.append(etree.tostring(element))
    
    # do for every pi
    for node in nodes:
      try: 
        int(objectify.fromstring(node).get("pi_id"))  
        ip = "10.1.1." + objectify.fromstring(node).get("pi_id")
        # send files to pi
        print("transferring data to pi with ip: " + ip)
        send_file(objectify.fromstring(node),ip)
      except Exception:
        ip = objectify.fromstring(node).get("pi_id")
        # send files to pi
        print("transferring data to pi with ip: " + ip)
        send_file(objectify.fromstring(node),ip) 
    print("all data transferred")   
