import os, sys, socket, platform, subprocess

from bin.socket_msg import socket_send_msg, socket_receive_msg
from bin.xml_and_log import parse_xml
from lxml import etree, objectify

#---------------------------------------------------------
#function: help_f
#---------------------------------------------------------
def help_f():
    print("------------------------------------------------------")
    print("Valid commands: ")
    print("help: shows list of commands")
    print("setxml arg: sets the xml file you want to use")
    print("connect: connects the server to the Pis")
    print("mentioned in the xml-file")
    print("transferdata: sends files referenced in the xml-file")
    print("to the specified Pis")
    print("start: starts set of code from xml")
    print("abort: aborts the running processes on the Pis")
    print("isconnected: shows, which Pis are connected")
    print("cleanfolder: delete the transfered data on all Pis")
    print("getlogs: transfer logs to server")
    print("rebootpi: reboot pi with id (or all)")
    print("restartdaemon: restart deamon of given id (or all)")
    print("exit: closes server script")
    print("clear: clears terminal")
    print("------------------------------------------------------")
    return

#---------------------------------------------------------
#function: exit_server
#arguments:
#  - sockets: array of sockets to send the reconnect message to
#---------------------------------------------------------
def exit_server(sockets):
    if sockets != -1:
        for soc in sockets:
            socket_send_msg(soc, "reconnect")
    sys.exit()

#---------------------------------------------------------
#function: start_second_window
#arguments:
#  - sockets: array of command sockets to get the ips from
#---------------------------------------------------------
def start_second_window(sockets):
    #check if sockets are connected
    if sockets == -1:
        return
    #get ids from sockets
    args = ""
    for soc in sockets:
        ip = soc.getpeername()[0]
        # id = ip.split(".")[-1]
        id = ip
        args = args + " " + str(id)

    distro_name = platform.linux_distribution()[0]
    if distro_name == 'debian':
        command = 'lxterminal --command="python2 debugwindow.py'+str(args)+'"'
    elif distro_name == 'Ubuntu':
        command = 'gnome-terminal --command="python2 debugwindow.py'+str(args)+'"'
    else:
        command = 'xterm -e python2 debugwindow.py'+str(args)

    sub = subprocess.Popen([command], shell = True, preexec_fn=os.setsid)
    sub = os.getpgid(sub.pid)

#---------------------------------------------------------
#function: ssh_command
#arguments:
#  - xmlfile: xml file to parse
#  - command: string with input from terminal
#---------------------------------------------------------
def ssh_command(xmlfile, command):
    target_pi_id = [] #holds list of target pi-ids to execute command on

    cmd = command.split() #split into command [0] and parameter [1] (specifies pi-id or "all")
    if len(cmd) < 2:
        print("Give target pi-id to restart as an argument (or all)")
        return

    if cmd[1] == 'all':
        if xmlfile == "":
            print("Set xml-file before using the 'all' option")
            return

        #parse xml to get pi-ids
        root_as_string = parse_xml(xmlfile)
        root = objectify.fromstring(root_as_string)
        nodes = []
        for element in root.getchildren():
            nodes.append(etree.tostring(element))

        #add every pi-id to list
        for node in nodes:

            target_pi_id.append(objectify.fromstring(node).get("pi_id"))
    else:
        for i in range(1,len(cmd)):
            print 'adding', cmd[i]
            target_pi_id.append(cmd[i])
        #if not (1 <= int(cmd[1]) <= 253):
        #    print("Invalid pi-id")
        #    return

        target_pi_id.append(cmd[1])

    for id in target_pi_id:
      try:
        int(id)
        errCode = 0
        if cmd[0] == "rebootpi":
            errCode = os.system("ssh -n -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@10.1.1."+id+" 'sudo shutdown -r 0 1>/dev/null 2>/dev/null'")
        elif cmd[0] == "restartdaemon":
            errCode = os.system("ssh -n -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@10.1.1."+id+" 'sudo systemctl restart asn_daemon 1>/dev/null 2>/dev/null'")
        elif cmd[0] == "killproccess":
            errCode = os.system(
                "ssh -n -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@10.1.1." + id + " 'sudo killall python 1>/dev/null 2>/dev/null'")

        if errCode != 0:
            print("Command failed (pi-id: "+id+")")
        else:
            print("Command successful (pi-id: "+id+")")
      except Exception:
        if cmd[0] == "rebootpi":
            errCode = os.system("ssh -t -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error  asn@"+id+" 'sudo shutdown -r 0 1>/dev/null 2>/dev/null'")
        elif cmd[0] == "restartdaemon":
            commandToRun = "ssh -t -o StrictHostKeyChecking=no  -o LogLevel=error  asn@" + id + " 'sudo systemctl restart asn_daemon 1>/dev/null 2>/dev/null'"
            errCode =os.system(commandToRun)
                # os.system("ssh -t -n -o StrictHostKeyChecking=no  -o LogLevel=error  asn@"+id+" 'sudo systemctl restart asn_daemon 1>/dev/null 2>/dev/null'")
            #print errCode
            #print commandToRun
        elif cmd[0] == "killproccess":
            errCode = os.system(
                "ssh -t -f  -o StrictHostKeyChecking=no  -o LogLevel=error  asn@" + id + " 'sudo killall python 1>/dev/null 2>/dev/null'")
        if errCode != 0:
            print("Command failed (pi-id: "+id+")")
            #print("Debug:", cmd)
        else:
            print("Command successful (pi-id: "+id+")")


