import cmd
import os
import logging
import fission
import time
import dispy
import glob

logger = logging.getLogger(__name__)

# TODO alles im detail durchgehen!
# REVIEW !!!


class FissionCMD(cmd.Cmd):
    intro = r"""
    \033[36m ___ ___ ___ ___ ___ ___  _  _ \u001b[0m    
    \033[36m| __|_ _/ __/ __|_ _/ _ \| \| |\u001b[0m    
    \033[36m| _| | |\__ \__ \| | (_) | .` |\u001b[0m    
    \033[36m|_| |___|___/___/___\___/|_|\_|\u001b[0m    
                                       
Client started.
See a list of commands and an introduction with 'help'"""
    prompt = "\033[36mFISSION: \u001b[0m"

    def __init__(self, user, network, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cluster = None

        self.network = network
        self.ssh_user = user

    def do_exit(self, arg):
        """Exits the FISSION Terminal.
        """
        if self.cluster:
            self.do_closecluster(arg)

        exit(0)

    def do_clear(self, arg):
        """Clears the Terminal.
        """
        os.system("clear")

    def emptyline(self):
        print("Unkown command, use 'help' for valid commands")

    def do_allocate(self, args):
        """Allocates all Jobs on available Nodes.
        """
        self.network.allocate_jobs()
        self.do_status("")

    def do_start(self, arg):
        """Starts the Jobs on the Nodes.
        """
        try:
            if not self.cluster:
                print("Start cluster first")
            else:
                # self.do_senddata(arg)
                try:
                    self.network.submit(self.cluster, self.ssh_user)
                    self.cluster.wait()
                except KeyboardInterrupt:
                    logger.info("User Interrupt, closing cluster...")
                    self.do_closecluster(arg)

        except Exception:
            logger.exception("Start method failed")

    def do_stop(self, arg):
        """Stop current computation.
        """
        self.do_closecluster(arg)

    def do_senddata(self, arg):
        """Transfer Data to Nodes.
        """
        if self.network.is_ready():
            self.network.send_files(user=self.ssh_user)
        else:
            print("Network not ready yet")

    def do_removedata(self, arg):
        """Remove data from Nodes.
        """
        self.network.delete_files(user=self.ssh_user)

    def do_reboot(self, arg):
        """Reboots all Nodes in network.
        """
        self.network.reboot(user=self.ssh_user)

    def do_status(self, arg):
        """Display cluster status. 
        """
        print(self.network)

        print("\n{:-<40}\n".format("Cluster "))
        if self.cluster:
            self.cluster.print_status()
        else:
            print("No cluster running. 'startcluster' first.")

    def do_startcluster(self, args):
        """Start the dispy cluster with all Nodes in the network. 
        """
        if self.cluster:
            print("Cluster already running.")

        elif self.network.nodes:
            dependencies = fission.manager.get_dependencies()  # [network]
            nodes = [node.ipv4_addr for node in self.network.nodes]
            self.cluster = dispy.JobCluster(pipe_wrapper_no_sync, nodes=nodes, depends=dependencies,
                                            cluster_status=self.network.status_callback,
                                            pulse_interval=1, ping_interval=10, ip_addr="192.168.4.1")
            # setup=daemon.setup, cleanup=daemon.cleanup)
            time.sleep(2)
        else:
            print("Please use 'setnodes' or 'setxml' first.")

    def do_closecluster(self, args):
        """Kills all running Jobs on Nodes and deletes the current cluster.
        """
        if self.cluster:
            cluster = self.cluster
            self.cluster = None
            cluster.close(timeout=1, terminate=True)
        else:
            print("No cluster running.")

    def _append_slash_if_dir(self, p, ending=None):
        if p and os.path.isdir(p) and p[-1] != os.sep:
            return p + os.sep
        else:
            if ending and (not p.endswith(ending)):
                return None
            else:
                return p

    def file_complete(self, text, line, begidx, endidx, ending=None):
        """Completer for setxml 
        """
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return  # arg not found

        fixed = line[before_arg+1:begidx]  # fixed portion of the arg
        arg = line[before_arg+1:endidx]
        pattern = arg + '*'

        completions = []
        for path in glob.glob(pattern):
            path = self._append_slash_if_dir(path, ending=ending)
            if path:
                completions.append(path.replace(fixed, "", 1))
        return completions
