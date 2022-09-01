import inspect
import json
import logging
import multiprocessing
import os
import pickle
import re
import shutil
import socket
import struct
import threading
import time
from pathlib import Path

import dispy

import fission.core.base
from fission.core.base import GROUPS, NODES
from fission.core.jobs import BaseJob
from fission.core.nodes import BaseNode, LocalNode, NodeInfo
from fission.remote.wrapper import pipe_wrapper_sync

logger = logging.getLogger(__name__)

class AllocationError(RuntimeError):
    pass

class Network():
    def __init__(self, user, jobs=None, nodes=None, pipes=None, name=None, debug=False, remote_root='', client_ip="localhost", pre_copy=False, port_offset=2000):
        """Class representing the network

        Keyword Arguments:
            jobs {list} -- Optional list of jobs (default: {[]})
            nodes {list} -- Optional list of nodes (default: {[]})
        """
        self.user = user
        self.remote_root = remote_root
        self.debug = debug
        self.cluster = None
        self.name = name
        self.debug_pipe = None
        self.client_ip = client_ip
        self.port_offset = port_offset
        self.pre_copy = pre_copy

        # necessary because default dict is a pointer
        if jobs == None:
            self.jobs = dict()
        else:
            self.jobs = jobs
        if nodes == None:
            self.nodes = dict()
        else:
            self.nodes = nodes
        if pipes == None:
            self.pipes = dict()
        else:
            self.pipes = pipes

        self.dispy_jobs = dict()
        self._shutdown = False
        self._finished = threading.Event()
        self._callback_lock = threading.Lock()
        self._local_is_reset = False

    def add_node(self, node):
        if isinstance(node, BaseNode):
            node = {node.ip: node}
            self.nodes.update(node)
        else:
            raise RuntimeError(
                f"Tried adding {type(node)} as node to network.")

    def add_job(self, job):
        if isinstance(job, BaseJob):
            job = {job.id: job}
            self.jobs.update(job)
        else:
            raise RuntimeError(f"Tried adding {type(job)} as job to network.")

    def send_files(self, nodes=[]):
        """Send job files to all or specific nodes

        Keyword Arguments:
            nodes {list} -- List of nodes. Runs for all Nodes when empty (default: {[]})
        """
        # check if specific nodes where given
        if not nodes:
            nodes = [n for n in self.nodes.values(
            ) if not isinstance(n, LocalNode)]

        for node in nodes:
            if self.pre_copy:
                if node.pre_copied:
                    continue
                jobs = self.jobs.values()
            else:
                jobs = [j for j in node.jobs if j.status == j.STOPPED]

            for job in jobs:
                print(f"Copying data for job with id {job.id}")

                scp_command = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error -pr {src} {user}@{ip}:{dest}"
                mkdir_command = "ssh {user}@{ip} 'mkdir -p {path}/fifo'"

                # logger.debug(f"Sending {job.DEPENDENCIES} to {node.ip}")

                error = 0
                # NOTE has to be changed when DEPENDENCIES get list
                if job.DEPENDENCIES:
                    # creating parent dir
                    os.system(mkdir_command.format(
                        user=self.user, ip=node.ip, path=self.remote_root))
                    # copying
                    error = os.system(scp_command.format(
                        src=job.DEPENDENCIES, user=self.user, ip=node.ip,
                        dest=Path(f"{self.remote_root}/{job.id}")))

                if error:
                    logger.warning(f"Copying {job} failed with code {error}")
                else:
                    logger.debug(f"Copying {job} succeeded")

            if self.pre_copy:
                node.pre_copied = True

    def delete_files(self, nodes=[]):
        """Delete all files from nodes. Including pipes.

        Keyword Arguments:
            user {str} -- User ssh connects to (default: {"asn"})
            nodes {list} -- List of nodes. Runs for all Nodes when empty (default: {[]})
        """
        # check if specific nodes where given
        if not nodes:
            nodes = [node for node in self.nodes.values(
            ) if GROUPS['LOCAL'] not in node.GROUPS]

        ssh_command = "ssh {user}@{ip} 'rm -r {path}' > /dev/null"

        for node in nodes:
            # print(f"Deleting data from {node.ip}.")

            logger.debug(f"Deleting data from {node.ip}.")

            # copying
            error = os.system(ssh_command.format(
                user=self.user, ip=node.ip, path=self.remote_root))
            # remove temp dirs

            if error:
                logger.warning(
                    f"Deleting data from {node.ip} returned with {error}.")
            else:
                logger.debug(f"Deleting data from {node.ip} succeeded.")

    def reboot(self, nodes=[]):
        """Reboot all Nodes

        Keyword Arguments:
            user {str} -- User ssh connects to (default: {"asn"})
            nodes {list} -- List of nodes. Runs for all Nodes when empty (default: {[]})
        """
        # check if specific nodes where given
        if not nodes:
            nodes = self.nodes.values()

        ssh_command = "ssh {user}@{ip} 'sudo reboot'"

        for node in nodes:
            logger.debug(f"Rebooting {node.ip}.")
            # copying
            error = os.system(ssh_command.format(user=self.user, ip=node.ip))
            # remove temp dirs
            if error:
                logger.warning(
                    f"Rebooting {node.ip} returned with {error}.")
            else:
                logger.debug(f"Rebooting {node.ip} succeeded.")

    def is_ready(self):
        """Returns if all Jobs are allocated

        Returns:
            bool -- Whether all Jobs are running or not
        """
        for job in self.jobs.values():
            if not job.allocated:
                return False
        return True

    def up(self, ip):
        """Set a node with given ip to up state

        Arguments:
            ip {str} -- ip of the node
        """
        try:
            return self.nodes[ip].open()
        except KeyError:
            raise RuntimeError(
                f"Node with {ip} does not exist in Network database.")

    def down(self, ip):
        """Set a node with given ip to down state

        Arguments:
            ip {str} -- ip of the node
        """
        try:
            return self.nodes[ip].close()
        except KeyError:
            raise RuntimeError(
                f"Node with {ip} does not exist in Network database.")

    def submit(self, cluster):
        """Submit all STOPPED jobs to given cluster.
        If pre_copy is set it will also wait until data transfer is complete.

        Arguments:
            cluster {JobCluster} -- Cluster to submit to
            user {str} -- ssh user
        """
        nodes = [node for node in self.nodes.values(
        ) if node.active and not isinstance(node, LocalNode)]

        if self.pre_copy:
            while not all(map(lambda x: x.pre_copied, nodes)):
                time.sleep(.25)

        # Copy data for DEAD jobs
        for node in nodes:
            if not self.pre_copy:
                self.send_files(nodes=[node])

        # Start DEAD jobs
        for node in nodes:
            jobs = [job for job in node.jobs if job.status in [
                job.STOPPED]]
            for job in jobs:
                print(f"Submitting {job} to {repr(node)}.")

                if self.pre_copy:
                    job_dependencies = []
                else:
                    job_dependencies = job.get_dependencies()

                job.dispy_job = cluster.submit_node(node.ip, job,
                                                    root=self.remote_root, debug=self.debug,
                                                    dispy_job_depends=job_dependencies)

        self.local_submit()

        # print(self)

    def local_submit(self):
        """Submits all LocalJobs.
        Basically meaning it starts the subprocesses for all LocalJobs.
        """
        # Get client node
        node = NODES[self.client_ip]

        # Check if there are any local jobs
        if node.jobs:
            def cwd_wrapper(func, cwd, *args, **kwargs):
                # this is used to change the cwd when using
                # multiprocessing instead of subprocess module
                os.chdir(cwd)
                func(*args, **kwargs)

            root = Path(f"{os.getcwd()}/{self.name}/local")

            if not self._local_is_reset:
                # clear directory for local jobs
                if root.exists():
                    shutil.rmtree(root)

                os.makedirs(root/"fifo", exist_ok=True)
                self._local_is_reset = True

            processes = []

            for job in node.jobs:
                if job.status == job.STOPPED:
                    # copy dependencies
                    dest = root/f"{job.id}/"
                    if job.DEPENDENCIES:
                        shutil.copytree(job.DEPENDENCIES, dest)
                    os.makedirs(dest, exist_ok=True)
                    # created subprocesses
                    args = (pipe_wrapper_sync,
                            f"{root}/{job.id}", job, str(root))
                    kwargs = {"debug": self.debug,
                            "ip_addr": self.client_ip, "log_level": "WARNING"}
                    # logger.warning(f"ARGS:{args} KWARGS:{kwargs}")
                    new_process = multiprocessing.Process(
                        target=cwd_wrapper, args=args, kwargs=kwargs, daemon=True)
                    processes.append(new_process)
                    job.status = job.RUNNING

            for p in processes:
                # start subprocesses
                p.start()

    def terminated(self, id):
        job = self._get_job_by_dispy_id(id)
        if job:
            job.status = job.STOPPED  # DEAD
        else:
            logger.warning(f"DispyJob {id} does not exist.")

    def restart(self, id):
        job = self._get_job_by_dispy_id(id)
        if job:
            job.status = job.RESTARTING
        else:
            logger.warning(f"DispyJob {id} does not exist.")

    def running(self, id):
        job = self._get_job_by_dispy_id(id)
        if job:
            job.status = job.RUNNING  # RUNNING
        else:
            logger.warning(f"DispyJob {id} does not exist.")

    def finished(self, id):
        job = self._get_job_by_dispy_id(id)
        if job:
            job.status = job.FINISHED  # FINISHED
        else:
            logger.warning(f"Could not find matching Job to dispy id {id}")
        if all([j.status == j.FINISHED for j in self.jobs.values()]):
            self._finished.set()
        else:
            logger.warning(f"DispyJob {id} does not exist.")

    def shutdown(self):
        """Closes attached dispy cluster if there is one and ignores any further
        incoming callbacks
        """
        logger.info("Shutting down Network...")
        self._shutdown = True
        self._finished.set()
        if self.cluster:
            self.cluster.close(timeout=1, terminate=True)

    def wait(self, timeout=None):
        """Waits until all jobs are finished or cluster is shutdown

        Keyword Arguments:
            timeout {float} -- Timeout for wait statement (default: {None})

        Returns:
            bool -- Whether shutdown was called (False) or cluster finished all jobs (True)
        """
        self._finished.wait(timeout)
        if self._shutdown:
            return False
        else:
            return True

    def _get_node_fewest_jobs(self, job):
        """Find node with fewest jobs.
        First in nodes in case of draw.

        Returns:
            Node -- Node with fewest jobs (None if nothing found)
        """
        for group in job.GROUPS:
            try:
                logger.debug(
                    f"Avail Nodes without active: {[n for n in group.nodes if  n.active]}")
                logger.debug(
                    f"Avail Nodes without full: {[n for n in group.nodes if not n.full()]}")
                logger.debug(
                    f"Avail Nodes without both: {[n for n in group.nodes ]}")
                logger.debug(
                    f"Avail Nodes: {[n for n in group.nodes if n.active and not n.full()]}")
                return min([n for n in group.nodes if n.active and not n.full()], key=lambda x: len(x.jobs))
            except ValueError:
                continue
        return None

    def _best_node_allocation(self, job, ssh):
        """Finds node with best parameters for a given job

        Returns:
            Node -- best found Node
            None -- if nothing found
        """
        try:
            # determines nodes to be redirected
            redirect_nodes = []
            for i in job.inputs:
                if i.source.allocated not in redirect_nodes and isinstance(i.source.allocated, BaseNode):
                    redirect_nodes.append(i.source.allocated)
            logger.debug(f" input jobs for {job}: {redirect_nodes}")
            for o in job.outputs:
                if o.destination.allocated not in redirect_nodes and isinstance(o.destination.allocated, BaseNode):
                    redirect_nodes.append(o.destination.allocated)
            logger.debug(f" input and output jobs for {job}: {redirect_nodes}")
            if ssh:
                for node in redirect_nodes:
                    if isinstance(node, LocalNode):
                        os.system(f"sudo batctl o 1>bat.txt 2>/dev/null")
                    else:
                        os.system(f"ssh {self.user}@{node.ip} 'sudo batctl o' 1>bat.txt 2>/dev/null")

                    node.batman_info()

            # initalized values for the calculation
            preference_nodes = []
            best_node = None
            max_value = 0
            x = len(redirect_nodes)
            if x:  # if zero skip and return _get_node_fewest_jobs()
                for group in job.GROUPS:
                    logger.debug(f" Checking group {group}")
                    for node in group.nodes:
                        logger.debug(f" Checking node {node} in group {group}")
                        # check if dispy info is available
                        if node.active and node.info["cpu"] and not node.full():
                            TQ = 0
                            # calculate TQ for all Nodes which have a connection with the job
                            for r_node in redirect_nodes:
                                # TQ to tiself not in BATMAN
                                if r_node == node:
                                    TQ += 255
                                else:
                                    for entry in r_node._routing_table:
                                        # find routing entry for current node
                                        if entry["mac"] == None:
                                            TQ += 255
                                            break
                                        elif entry["mac"] == node.mac:
                                            TQ += int(entry["TQ"])
                                            break
                            TQ /= x  # average TQ
                            #prepare NodeInfo objects for possible preference
                            preference_nodes.append(NodeInfo(
                                node, node.info["cpu"], node.info["memory"], node.info["disk"], node.info["swap"], TQ))
                            # calculate decision value
                            value = (
                                (TQ/255)*100 + node.info["cpu"] + (100-node.info["swap"]))/3

                            _avail_jobs = node.max_jobs - len(node.jobs)
                            value *= _avail_jobs

                            if(max_value < value):
                                best_node, max_value = node, value
                                logger.debug(f" selecting best node  {best_node}")

                        else:
                            logger.debug(
                                f"Node {node.ip} has no Dispy informations."
                                f"\nCurrent info: "
                                f"\nactive: {node.active} and CPU: {node.info['cpu']}\n full {node.full()}")
                    # if a node is found return, or search in other group
                    if hasattr(job, "preference"):
                        nodeinfo = job.preference(preference_nodes)
                        # Sanity check
                        if isinstance(nodeinfo, NodeInfo):
                            if nodeinfo in preference_nodes:
                                if nodeinfo._node in group.nodes:
                                    return nodeinfo._node
                    if best_node:
                        # Catch case if all nodes are full
                        return best_node
                return self._get_node_fewest_jobs(job)
            else:
                return self._get_node_fewest_jobs(job)
        except:
            # logger.warining(
            #     "No restart jobs given, or some other error occured!")
            return self._get_node_fewest_jobs(job)
    def has_inactive_nodes(self):
        debug = ""
        for n in self.nodes.values():
            if not n.active():
                debug+=f"Node {n} is still inactive\n"
        if debug:
            #logger.debug(debug)
            return True
        return False

    def allocate_jobs(self, ssh=True, timeout=-1):
        """Allocate all none allocated jobs

            Returns: Nodes with new allocated jobs
        """
        # logger.debug(f"Before Allocating Jobs Check Network status\n {self.__repr__()}")
        try:
            self._callback_lock.acquire(timeout=timeout)
            nodes = []
            to_assign_jobs = [j for j in self.jobs.values(
            ) if not j.allocated and j.status != j.FINISHED]
            for job in to_assign_jobs:
                node = None
                if hasattr(job, "DEFAULT_NODE") and job.DEFAULT_NODE:
                    try:
                        _node = self.nodes[job.DEFAULT_NODE]
                        if _node.full():
                            raise AllocationError
                        else:
                            node = _node

                    except KeyError:
                        logger.info(f"{job}: could not find default node {job.DEFAULT_NODE}.")
                    except AllocationError:
                        logger.info(f"{job}: default node is full.")

                if node == None:
                    if True:
                        node = self._best_node_allocation(job, ssh)
                    else:
                        node = self._get_node_fewest_jobs(job)
                # if node and restart_nodes:
                #     redirect_jobs.append((job, node))

                if node:
                    node.add_job(job)
                    nodes.append(node)
                else:
                    logger.debug(self.__repr__())
                    logger.warning(f"No available node for allocating {job.id}.")
                    raise AllocationError(f"No available node for allocating {job}.")

            if True:
                # generate command dict for redirects and resets
                reset = False
                commands = dict()
                for job in to_assign_jobs:

                    logger.debug(f"Creating commands for {job}")
                    # flag as source failure -> reset needed
                    if job.is_source() or job.is_async():
                        reset = True

                    # handle inputs
                    for i in job.inputs:
                        effected_job = i.source
                        # pass if job was just reallocated
                        if effected_job in to_assign_jobs:
                            # logger.warning(f"Skipping {i}@{job}")
                            continue
                        commands.setdefault(effected_job.id, dict())
                        commands[effected_job.id].setdefault("REDIRECT", dict())
                        commands[effected_job.id]["REDIRECT"][i.id] = job.allocated.ip

                    # handle outputs
                    for o in job.outputs:
                        # pass if job was just reallocated
                        effected_job = o.destination
                        if effected_job in to_assign_jobs:
                            # logger.warning(f"Skipping {o}@{job}")
                            continue
                        #logger.debug(f"{[o.destination.allocated, job.allocated]}")
                        if effected_job.allocated is job.allocated:
                            commands.setdefault(effected_job.id, dict())
                            commands[effected_job.id].setdefault(
                                "REDIRECT", dict())
                            commands[effected_job.id]["REDIRECT"][o.id] = effected_job.allocated.ip

                # send reset if
                if reset:
                    source_jobs = [j for j in self.jobs.values() if (
                        j.is_source() or j.is_async())]
                    # logger.info(f"Source Jobs: {source_jobs}")
                    for source in source_jobs:
                        if source not in to_assign_jobs:
                            commands.setdefault(source.id, dict())
                            # TODO send timestamp
                            commands[source.id]["RESET"] = True

                # logger.info(f"Sending following commands: {commands}")
                # create and spawn according thread
                for job_id, command in commands.items():
                    job = self.jobs[job_id]
                    # if job.status == job.RUNNING:
                    args = (job, command)
                    threading.Thread(target=self.send_redirect,
                                    args=args, daemon=True).start()

            self.update_debug_window()
            if nodes:
                logger.info(f"Network state:\n{self}\n")
            return nodes
        finally:
            self._callback_lock.release()

    def _get_job_by_dispy_id(self, dispy_id):
        """Internal use to retrieve a FISSION job from its dispy id

        Arguments:
            dispy_id {int} -- dispy id a FISSION job is executed with

        Returns:
            BaseJob -- The associated FISSION job, if there isn't any it is None
        """
        for job in [job for job in self.jobs.values() if job.dispy_job]:
            if dispy_id == job.dispy_job.id:
                return job
        return None

    def status_callback(self, status, node, job):
        """Handling callbacks from JobCluster

        Arguments:
            status {dispy status} -- New status (Job status or node status)
            node {dispy.DispyNode} -- Updated node
            job {dispy.DispyJob} -- Updated job
        """
        # skip execution when network bis been shutdown
        if self._shutdown:
            return

        if status == dispy.DispyNode.Initialized:
            if node.ip_addr not in self.nodes.keys():
                logger.info(f"Created new BaseNode for {node.ip_addr}.")
                _node = BaseNode(node.ip_addr)
                _node.max_jobs = node.cpus
                GROUPS["ALL"].add_node(_node)
                self.nodes[node.ip_addr] = _node

            logger.info(
                "Node {0.ip_addr} showed up with {0.avail_cpus} CPUs.".format(node))
            self.up(node.ip_addr)
            if self.pre_copy:
                self.send_files(nodes=[self.nodes[node.ip_addr]])

        elif status == dispy.DispyNode.Closed:
            closed_jobs = self.down(node.ip_addr)
            logger.warning(
                f"Node {node.ip_addr} closed with {closed_jobs} Jobs.")
            if self.cluster and not self.is_ready():
                jobs = []
                for j in closed_jobs:
                    for i in j.inputs:
                        jobs.append(i.source)
                    for o in j.outputs:
                        jobs.append(o.destination)
                for i in jobs:
                    if i.dispy_job:
                        pass
                        # self.cluster.cancel(i.dispy_job)
                        # self.restart(i.dispy_job.id)
                try:
                    nodes = self.allocate_jobs()
                    logger.debug(f"Remaining Jobs allocated on {nodes} Nodes.")
                    self.submit(self.cluster)
                except AllocationError:
                    logger.error("Allocation error, shutting down...")
                    self.shutdown()
                    self._finished.set()

        elif status == dispy.DispyNode.AvailInfo:
            try:
                # logger.debug(f"Heartbeat from Node {node.ip_addr}.")
                self.nodes[node.ip_addr].info = [node.avail_info.cpu,
                                                 node.avail_info.memory,
                                                 node.avail_info.disk,
                                                 node.avail_info.swap]
            except AttributeError:
                logger.exception(
                    f"Node {node.ip_addr} has no psutil installed.")

        # JOBS
        elif status == dispy.DispyJob.Abandoned:
            logger.debug(f"DispyJob {job.id} abandoned.")

        elif status == dispy.DispyJob.Finished:
            logger.info(
                f"DispyJob with ID {job.id} finished.")
            if job.result:
                logger.debug(f"Result: {job.result}")
            if job.stdout:
                logger.debug(f"Stdout: {job.stdout}")
            self.finished(job.id)

        elif status == dispy.DispyJob.Created:
            pass
            # logger.debug(f"DispyJob created with ID {job.id}")

        elif status == dispy.DispyJob.Running:
            logger.debug(f"DispyJob running with ID {job.id}")
            self.running(job.id)

        elif status == dispy.DispyJob.Terminated:
            logger.debug(
                f"Job {self._get_job_by_dispy_id(job.id)} terminated on node {job.ip_addr}")
            if job.exception:
                logger.debug(f"With error:\n{job.exception}")
            self.terminated(job.id)

        elif status == dispy.DispyJob.Cancelled:
            logger.debug(
                f"DispyJob with ID {job.id} cancelled.\nResult: {job.result}\nStdout: {job.stdout}"
            )
            self.terminated(job.id)
            # self.submit(self.cluster, self.ssh_user)

        else:
            if node:
                logger.warning(
                    f"Unexpected callback from {node.ip_addr} with status {status}")
            else:
                logger.warning(
                    f"Unexpected callback from {job.ip_addr} with status {status}")
                if job.stdout:
                    logger.warning(f"Out: {job.stdout}")
                if job.exception:
                    logger.warning(f"Traceback: {job.exception}")

    def update_debug_window(self):
        """Sends a update of the network in JSON format to 
        the debug window via the debug_pipe.
        """
        if self.debug_pipe:
            try:
                out = []
                for job in sorted(self.jobs.values(), key=lambda x: x.id):
                    if job.allocated:
                        out.append({'name': f"{job}", 'ip': f"{job.allocated.ip}",
                                    'port': self.port_offset - (job.id * 2)})
                self.debug_pipe.write(json.dumps(out) + '\n')
                self.debug_pipe.flush()
            except BrokenPipeError:
                logger.warning("Debug Window pipe broke, did you close it?")
                self.debug_pipe = None

    def send_redirect(self, job, command):
        if command:
            node = job.allocated
            port = self.port_offset-(job.id*2 - 1)
            logger.info(f"Sending redirect message: {command} to {job}")
            sock = socket.create_connection((node.ip, port), timeout=2)
            data = json.dumps(command).encode('utf-8')
            sent = sock.send(data)
            # logger.debug(f"Sent {sent} bytes.")
            sock.shutdown(socket.SHUT_WR)
            sock.close()

    def __str__(self):
        out = "{cluster}\n{allocated}/{jobs} jobs allocated\n{running} jobs running\n{finished} jobs finished\n{avail}/{nodes} nodes available\n\n".format(
            cluster=repr(self),
            allocated=len([j for j in self.jobs.values() if j.allocated]),
            running=len([j for j in self.jobs.values()
                         if j.status == j.RUNNING]),
            finished=len([j for j in self.jobs.values()
                          if j.status == j.FINISHED]),
            jobs=len(self.jobs.values()),
            avail=len([n for n in self.nodes.values() if n.active]),
            nodes=len(self.nodes)
        )

        out += "\n".join([str(n) for n in self.nodes.values()])
        return out

    def __repr__(self):
        debug = "Nodes\n"
        for i in self.nodes.values():
            debug+=f"node {i} : {i.active()} Group: {[j.name for j in i.GROUPS]}\n"
        debug +="\n Jobs\n"
        for i in self.jobs.values:
            debug+=f"job {i} : Group: {[g.name for g in g.GROUPS]}"
        return "Network: {} Nodes | {} Jobs".format(len(self.nodes), len(self.jobs))
