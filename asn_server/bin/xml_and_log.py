import os, socket, datetime
from lxml import etree, objectify

#------------------------------------------------------------
# This class is for coloring purposes
#------------------------------------------------------------
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
#---------------------------------------------------------
#function: parse_xml
#arguments:
#  - xml_file: path with name of the xml file to read
#return values:
#  - xml: content of the xml file
#---------------------------------------------------------
def parse_xml(xml_file):
    with open(xml_file) as file:
        xml = file.read()
        return xml

#---------------------------------------------------------
#function: set_xml
#arguments:
#  - command: complete string input of the terminal
#return values:
#  - xmlfile: path with name of the xmlfile to read -
#    send empty if file does not exists
#---------------------------------------------------------
def set_xml(command):
    parts = command.split()
    if len(parts) < 2:
        print("Pass path to the xml-file as an argument")
        return ""
    xmlfile = parts[1]
    if os.path.exists(xmlfile):
        check_alive(xmlfile)
        print (bcolors.OKGREEN+xmlfile+ " is set as xml-file"+ bcolors.ENDC) 
        return xmlfile
    else:
        print("Xml file not found")
        return ""
#---------------------------------------------------------
#function: lset_xml
#arguments:
#  - command: complete string input of the terminal
#return values:
#  - xmlfile: path with name of the xmlfile to read -
#    send empty if file does not exists
# Note: Same as set_xml but without checking reachability
#---------------------------------------------------------
def l_set_xml(command):
    parts = command.split()
    if len(parts) < 2:
        print("Pass path to the xml-file as an argument")
        return ""
    xmlfile = parts[1]
    if os.path.exists(xmlfile):
        print(xmlfile + " was set as xml-file")
        return xmlfile
    else:
        print("Xml file not found")
        return ""
#---------------------------------------------------------
#function: create_log
#arguments:
#  - path: string with path of the logfile
#---------------------------------------------------------
def create_log(path):
    global logfile
    logfile = open(path,'a',0)

#---------------------------------------------------------
#function: log
#arguments:
#  - message: string with message to write to logfile
#---------------------------------------------------------
def log(message):
    print(message)
    logfile.write(message+'\n')

#---------------------------------------------------------
#function: get_logfiles
#arguments:
#  - sockets: array of sockets to get logfiles from
#---------------------------------------------------------
def get_logfiles(sockets):
    if sockets != -1:
        #get timestamp
        time = datetime.datetime.now()
        timestamp = str(time.day)+"_"+str(time.month)+"_"+str(time.hour)+"_"+str(time.minute)+"_"+str(time.second)
        #create new folder
        os.system("mkdir logfiles/"+timestamp)
        daemonpath = "/home/asn/asn_daemon/logfiles/*"
        for soc in sockets:
            ip = soc.getpeername()[0]
            id = ip.split(".")[-1]
            id_folder = "pi_"+str(id)
            os.system("mkdir logfiles/"+timestamp+"/"+id_folder)
            os.system("scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@"+str(ip)+":"+daemonpath+" logfiles/"+timestamp+"/"+id_folder+"/")
        print("all logs transferred")
    else:
        print("Sockets not connected yet")

def check_alive(xmlfile):
    # parse xml to get pi-ids
    target_pi_id = []
    root_as_string = parse_xml(xmlfile)
    root = objectify.fromstring(root_as_string)
    nodes = []
    for element in root.getchildren():
        nodes.append(etree.tostring(element))

    # add every pi-id to list
    for node in nodes:
        target_pi_id.append(objectify.fromstring(node).get("pi_id"))

    for id in target_pi_id:
      try:
        int(id)
        errCode = 0
        errCode = os.system("ssh -t  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@10.1.1."+id+" 'sudo systemctl restart asn_daemon 1>/dev/null 2>/dev/null'")
        if errCode != 0:
                        print (bcolors.WARNING + "Warning - Please check the reachability and make sure that daemon is running\\ or try the killproccess command"+ bcolors.ENDC) 
      
      except Exception:
        errCode = os.system("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error -t  asn@"+id+" 'sudo systemctl restart asn_daemon 1>/dev/null 2>/dev/null'")
        if errCode != 0:
            print (bcolors.WARNING + "Warning - Please check the reachability  and make sure that daemon is running\n or try the killproccess command"+ bcolors.ENDC) 
