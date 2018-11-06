import os, sys, readline, re


from bin.socket_msg import socket_send_msg, socket_receive_msg
from bin.xml_and_log import set_xml, create_log, log, get_logfiles
from bin.file_managment import delete, send_data
from bin.process_managment import abort, start,gentleAbort
from bin.connection import connect, is_online
from bin.core_functionality import help_f, exit_server, start_second_window, ssh_command
from bin.optlib2_orig import optimizeAllocation,heuristicAllocation

#define global variable for logfile
logfile = 0
'''files '''
nodesfile = 'bin/simParam/nodeSim_' + str(0) + '.csv'
# appSim
appSimFile = 'bin/simParam/appsim_11'+'.csv'
# edges
arcsfile = 'bin/simParam/arcs_' + str(0) + '.csv'
# vnf
chainsfile = 'bin/simParam/chain_' + str(1) + '.csv'

COMMANDS = ["exit", "help","clear","start","abort","cleanfolder","setxml","connect","transferdata","isconnected","getlogs","rebootpi","restartdaemon","showxml","allocate","terminate","killproccess"]
RE_SPACE = re.compile('.*\s+$', re.M)

class Completer(object):
    def __init__(self):
        self.history_file = os.path.join('./', '.asn_history')
        try:
            readline.read_history_file(self.history_file)
        except IOError:
            open(self.history_file, 'a').close()

    def __del__(self):
        print'read'
        readline.write_history_file(self.history_file)

    def _listdir(self, root):
        "List directory 'root' appending the path separator to subdirs."
        res = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                name += os.sep
            res.append(name)
        return res

    def _complete_path(self, path=None):
        "Perform completion of filesystem path."
        if not path:
            return self._listdir('.')
        dirname, rest = os.path.split(path)
        tmp = dirname if dirname else '.'
        res = [os.path.join(dirname, p)
                for p in self._listdir(tmp) if p.startswith(rest)]
        # more than one match, or single match which does not exist (typo)
        if len(res) > 1 or not os.path.exists(path):
            return res
        # resolved to a single directory, so return list of files below it
        if os.path.isdir(path):
            return [os.path.join(path, p) for p in self._listdir(path)]
        # exact file match terminates this completion
        return [path + ' ']

    def complete_setxml(self, args):
        "Completions for the 'setxml' command."
        if not args:
            return self._complete_path('.')
        # treat the last arg as a path and complete it
        return self._complete_path(args[-1])

    def complete(self, text, state):
        "Generic readline completion entry point."
        buffer = readline.get_line_buffer()
        line = readline.get_line_buffer().split()
        # show all commands
        if not line:
            return [c + ' ' for c in COMMANDS][state]
        # account for last argument ending in a space
        if RE_SPACE.match(buffer):
            line.append('')
        # resolve command to the implementation function
        cmd = line[0].strip()
        if cmd in COMMANDS:
            impl = getattr(self, 'complete_%s' % cmd)
            args = line[1:]
            if args:
                return (impl(args) + [None])[state]
            return [cmd + ''][state]
        results = [c + '' for c in COMMANDS if c.startswith(cmd)] + [None]
        return results[state]

comp = Completer()
# we want to treat '/' as part of a word, so override the delimiters
readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(comp.complete)

if __name__ == "__main__":
    
    create_log("logfiles/server.log")
    cmd_socs = -1
    msg_socs = -1
    xmlfile = ""
    connected = 0
    
    #welcome sequence
    print("------------------------------------------------------")
    print("""
          _   _  _  ___ _ _ ___ _   _  
         | \_/ |/ \| o \ | | __| | / \ 
         | \_/ | o |   / V | _|| |_ o )
         |_| |_|_n_|_|\\\\\\_/|___|___\_/ 
     
        """)
    print("------------------------------------------------------")
    print("Server started.")
    print("See a list of commands and an introduction with 'help'")

    # main-loop
    while(1):
        try:
            command = raw_input( u"\033[95mMARVELO: \u001b[0m")
            if not command.strip():
                continue
        except:
            command = "exit"
        readline.write_history_file(comp.history_file)

        if command == "exit":
            try:
                exit_server(cmd_socs)
            except Exception as e:
                log("exit method failed")
                log(type(e))
                log(e)

        elif command == "help":
            help_f()

        elif command == "clear":
            os.system("clear")

        elif command == "start":
            try:
                start(xmlfile,cmd_socs)
            except Exception as e:
                log("start method failed")
                log(type(e))
                log(e)

        elif command == "abort":
            abort(cmd_socs)
        elif command == "terminate":
            gentleAbort(cmd_socs)
        elif command == "cleanfolder":
            delete(cmd_socs)
        
        elif command[:6] == "setxml":
            xmlfile = set_xml(command)

        elif command == "connect":
            try:
                cmd_socs,connected = connect(xmlfile,connected,cmd_socs)
            except Exception as e:
                log("connect method failed")
                log(e.__traceback__)
                log(type(e))
                log(e)
            try:
                start_second_window(cmd_socs)
            except Exception as e:
                log("start of second window method failed")
                log(type(e))
                log(e)

        elif command == "transferdata":
            send_data(xmlfile,cmd_socs)
        
        elif command == "isconnected":
            is_online(cmd_socs)

        elif command == "getlogs":
            get_logfiles(cmd_socs)

        elif command[:8] == "rebootpi":
            ssh_command(xmlfile, command)

        elif command[:13] == "restartdaemon":
            ssh_command(xmlfile, command)

        elif command[:12] == "killproccess":
            ssh_command(xmlfile, command)

        elif command == "showxml":
            if xmlfile!='':
                os.system("python bin/xml_viewer.py "+xmlfile+" &")
            else:
                print 'please set an xml path using \'setxml\' command'

        elif command == "allocate":
            print '*** Start Allocation Process ** '
            #gitos.system("python bin/optlib2.py")
            #optimizeAllocation()
            heuristicAllocation()
            xmlfile = "bin/simParam/allocation.xml"
            print '*** Finished Allocation Process ** '



        else:
            print("unkown command, use 'help' for valid commands")
