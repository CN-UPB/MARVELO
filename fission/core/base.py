import inspect
import logging
import numbers
import os
import pickle
import re
import struct
from inspect import isgeneratorfunction, signature
from itertools import count

import dispy
from dispy import NodeAllocate

logger = logging.getLogger(__name__)

# Cache for all groups {'name': <obj>}
GROUPS = {}

# Cache for all nodes {'ip': <obj>}
NODES = {}

# Cache for all pipes {id: <obj>}
PIPES = {}

# Cache for all jobs {id: <obj>}
# and counter for job ids
JOBS = {}
_ID = count(1)


def reset():
    """Clears all chache and resets id counter for jobs.
    """
    global GROUPS, NODES, PIPES, JOBS, _ID
    GROUPS = {}
    NODES = {}
    PIPES = {}
    JOBS = {}
    _ID = count(1)
    logger.info("Cleared cache and reset counter.")


class MetaJob(type):
    """Metaclass for all Jobs.
    Does some sanity checks on all classes inheriting from BaseJob.
    """
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        if not isinstance(new_cls.HEAD, bool):
            raise RuntimeError(f"{cls.__name__}: HEAD must be bool.")

        try:
            assert new_cls.STOPPED == 0
            assert new_cls.RUNNING == 1
            assert new_cls.RESTARTING == 2
            assert new_cls.FINISHED == 3
        except AssertionError:
            raise RuntimeError("Do not change existing Job states!")

        return new_cls


class MetaPipe(type):
    """Metaclass for all Pipes.
    Does some sanity checks on all classes inheriting from BasePipe.
    """
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        # sanity checking new Pipes
        if not (name == "LoaderPipe"):
            if isinstance(new_cls.BLOCK_COUNT, str):
                pass
            elif isinstance(new_cls.BLOCK_COUNT, int):
                if new_cls.BLOCK_COUNT < 1:
                    raise RuntimeError(f"BLOCK_COUNT of {name} must be >= 1")
            else:
                raise RuntimeError(
                    f"BLOCK_COUNT of {name} must be str or int.")

            if new_cls.BLOCK_SIZE < 1:
                raise RuntimeError(f"BLOCK_SIZE of {name} must be >= 1")

        for j in cls.SOURCE_JOBS + cls.DESTINATION_JOBS:
            if not isinstance(j, BaseJob):
                raise RuntimeError(
                    f"Source or destination jobs of {name} include illegal object ({j})")

        return new_cls


class BaseJob(metaclass=MetaJob):
    """BaseJob for all Jobs.
    Defines the least amount of functionality a Job must have.
    """
    # possible job states
    STOPPED = 0
    RUNNING = 1
    RESTARTING = 2
    FINISHED = 3

    # default node (bypasses GROUPS)
    DEFAULT_NODE = None

    # the group of the Job
    GROUPS = "ALL"

    # Whether to pass the head
    HEAD = False

    # Maximal queue length. Values <= 0 equal infinite
    MAX_QUEUE = 0

    CREATES_SUBPROCESS = False

    def __new__(cls, *args, id=None, **kwargs):
        # return existing job if id is given and exists
        if id:
            if id in JOBS.keys():
                return JOBS[id]
            else:
                raise RuntimeError(f"Job with given id ({id}) does not exist.")
        else:
            new_job = super().__new__(cls)

            # set the job id and other attr of the new object before returning it
            new_id = next(_ID)
            new_job.id = new_id
            new_job.status = cls.STOPPED
            new_job.allocated = None
            new_job.dispy_job = None
            new_job.inputs = []
            new_job.outputs = []
            JOBS[new_id] = new_job
            return new_job

    def __init__(self, inputs=None, outputs=None, *args, **kwargs):
        """Defines basic behavior for a Job.
        Does nothing in its 'run' method, therefore functionality has
        to be implemented by overriding the 'run' method.
        This class caches its object in the module variable JOBS.
        Therefore calls with the same id result in the exact same object!
        To clear the cache call the function 'reset' of the 'fission.core.base'.
        This will clear the cache for all Nodes, Jobs, Pipes and Groups.

        In addition this class runs a counter to set Job ids if it is not passed.
        This will create a new Job object and cache it.

        Arguments:
            inputs {list} -- A list of input Pipe objects (default: {None})
            outputs {list} -- A list of output Pipe objects (default: {None})
        """
        # setting pipe src and dest
        if inputs:
            for input in inputs:
                input.destination = self

        if outputs:
            for output in outputs:
                output.source = self

        if not self.inputs and inputs:
            self.inputs = inputs
        if not self.outputs and outputs:
            self.outputs = outputs

        self.head = None
        self.in_heads = [None]*len(self.inputs)
        self.out_heads = [None]*len(self.outputs)

        # load class attributes into object
        self.GROUPS = self.GROUPS

        self.HEAD = self.HEAD

        self.MAX_QUEUE = self.MAX_QUEUE
        self.CREATES_SUBPROCESS = self.CREATES_SUBPROCESS

    def allocate(self, node):
        """Allocate to node

        Arguments:
            node {Node} -- Node the job gets allocated to
        """
        if self.allocated:
            raise RuntimeError(
                f"Job {self} already allocated to {self.allocated}")

        if isinstance(node, BaseNode):
            self.allocated = node
        else:
            raise RuntimeError(f"You can not allocate a job to {type(node)}.")

    def deallocate(self):
        """Deallocate the job from its Node
        """
        self.allocated = None
        if self.status != self.FINISHED:
            self.status = self.STOPPED

    def start(self, seperate_job_pipes=False, *args, **kwargs):
        """This method is called when a job starts.
        By default it calls 'setup' and 'run' and passes all
        arguments.
        """
        self.setup(*args, seperate_job_pipes=seperate_job_pipes, **kwargs)
        self.run(*args, **kwargs)

    def setup(self, root, seperate_job_pipes=False, *args, **kwargs):
        """Setup before executing the Job.
        Includes creating pipes and sanity checking.

        Arguments:
            user {str} -- The user the Job is run by.
        """
        import os
        import stat

        path = root

        assert os.path.isdir(f"{path}/fifo")
        # Check if pipes exist and are indeed fifo
        for pipe in self.inputs + self.outputs:
            if seperate_job_pipes:
                pipe_path = f"{path}/fifo/{self.id}/{pipe.id}.fifo"
            else:
                pipe_path = f"{path}/fifo/{pipe.id}.fifo"
            assert os.path.exists(pipe_path)
            assert stat.S_ISFIFO(os.stat(pipe_path).st_mode)

        os.makedirs(f"{path}/{self.id}", exist_ok=True)
        assert os.path.isdir(f"{path}/{self.id}")

    def run(self, *args, **kwargs):
        """This function defines the core functionality of a job.
        """
        raise NotImplementedError

    def is_source(self):
        """Checks if Job has any inputs.

        Returns:
            bool -- Whether Job has inputs (False) or not (True)
        """
        return not bool(self.inputs) and bool(self.outputs)

    def is_sink(self):
        """Checks if Job has any inputs.

        Returns:
            bool -- Whether Job has inputs (False) or not (True)
        """
        return bool(self.inputs) and not bool(self.outputs)

    def is_connector(self):
        """Checks if Job has any inputs.

        Returns:
            bool -- Whether Job has inputs (False) or not (True)
        """
        return bool(self.inputs) and bool(self.outputs)

    def is_async(self):
        """Checks if all inputs are marked as ASYNC.
        This leads for a job to act like a source

        Returns:
            [type] -- [description]
        """
        return all(map(lambda x: x.ASYNC, self.inputs))

    def get_dependencies(self):
        job_modules = []
        pipe_cls = []
        for pipe in self.inputs + self.outputs:
            pipe_cls.extend(type(pipe).mro()[:-1][::-1])

        mros = type(self).mro()[:-1] + \
            type(self.allocated).mro()[:-1] + pipe_cls
        for cls in mros:
            module = inspect.getmodule(cls)
            if module.__name__ == "builtins":
                continue
            job_modules.append(module)

        if hasattr(self, '_modules'):
            job_modules.extend(self._modules)

        return job_modules

    def __getstate__(self):
        """Defines behavior when a object is pickled.
        E.g. removed unpickleable attributes from object.

        Returns:
            dict -- Represents the state of the object
        """
        state = self.__dict__.copy()

        # delete unnecessary or unpickleable data
        del state["status"]
        del state["dispy_job"]
        del state["GROUPS"]

        try:
            del state['_modules']
        except KeyError:
            pass

        return state

    def __setstate__(self, state):
        """Takes the output of __getstate__ to
        restore an objects state.

        Arguments:
            state {dict} -- The state which should be restored
        """
        self.__dict__.update(state)

    def __str__(self):
        return "{0.__class__.__name__} {0.id}".format(self)

    def __repr__(self):
        return str(self)


class BasePipe(metaclass=type):
    """BasePipe for all Pipes.
    Defines the least amount of functionality a Pipe must have.
    """
    # Block size in bytes or String if custom
    BLOCK_SIZE = 1
    # How many blocks are needed on the output side for processing
    BLOCK_COUNT = 1

    ASYNC = False

    # List of allowed source jobs
    SOURCE_JOBS = []
    # List of allowed destination jobs
    DESTINATION_JOBS = []

    def __new__(cls, id=None):
        # return existing job if id is given and exists
        if id:
            if id and id in PIPES.keys():
                pipe = PIPES[id]
                if not type(pipe) is cls:
                    raise RuntimeError(
                        f"Pipe with id {id} was called on {cls} and is {type(pipe)}")
                return PIPES[id]

            else:
                new_pipe = super().__new__(cls)

                # set the job id of the new object before returning it
                new_pipe.id = id
                new_pipe._source = None
                new_pipe._destination = None
                new_pipe._head_size = 1
                PIPES[id] = new_pipe
                return new_pipe
        else:
            return super().__new__(cls)

    def __init__(self, id):
        """Defines basic behaviour for a Job.
        Does nothing in its 'run' method, therefore functionality has
        to be implemented by overriding the 'run' method.
        This class caches its object in the module variable PIPES.
        Therefore calls with the same id result in the exact same object!
        To clear the cache call the function 'reset' of the 'fission.core.base'.
        This will clear the cache for all Nodes, Jobs, Pipes and Groups.

        Arguments:
            id {int} -- A unique id for a Pipe
        """
        # load class attributes into object
        # Makes pickle them easier
        self.BLOCK_SIZE = self.BLOCK_SIZE
        self.BLOCK_COUNT = self.BLOCK_COUNT
        self.SOURCE_JOBS = self.SOURCE_JOBS
        self.DESTINATION_JOBS = self.DESTINATION_JOBS
        self.ASYNC = self.ASYNC

    def pack(self, data):
        """This function is meant to be overridden.
        It specifies actions to be done before sending data over 
        the network/pipe. Useful for PythonJobs.

        Arguments:
            data {-} -- Data returned by the PythonJob

        Returns:
            bytes -- A bytes representation of data, passed to 'unpack'
        """
        return data

    def unpack(self, data):
        """This function is meant to be overridden.
        It specifies actions to be done before passing received bytes
        to the underlying PythonJob.

        Arguments:
            data {bytes} -- Received bytes from 'pack'

        Returns:
            - -- Data passed to the PythonJob
        """
        return data

    def read_head(self, file_obj):
        size = self._head_size
        return int.from_bytes(file_obj.read(size), byteorder="big")

    def write_head(self, file_obj, head):
        size = self._head_size
        return file_obj.write(head.to_bytes(size, byteorder="big"))

    def read(self, file_obj):
        """Read from given file_obj and serialize it if
        given.

        Arguments:
            file_obj {File} -- File object of file to read from (openend in binary)
            pipe {Pipe} -- Assotiated pipe

        Keyword Arguments:
            serializer {[type]} -- [description] (default: {None})
        """
        _data = file_obj.read(self.BLOCK_SIZE)

        if not _data:
            exit(0)

        #print(pipe.BLOCK_COUNT, pipe.BLOCK_SIZE, data)
        return _data

    def read_wrapper(self, file_obj):
        """This method is called by the job wrapper.
        By default it just read BLOCK_SIZE bytes from the pipe.
        Overriding this allows you to implement custom protocols.
        See PicklePipe and JSONPipe as examples.

        Arguments:
            file_obj {file} -- Pipe openend in binary mode

        Returns:
            bytes -- data
        """
        return self.read(file_obj)

    def write(self, file_obj, data):
        """Write data to given file_obj

        Arguments:
            file_obj {file_obj} -- File object to write to (needs to be opened in binary)
            data {bytes} -- Date to write to file_obj

        Returns:
            [type] -- [description]
        """
        while True:
            try:
                out_bytes = file_obj.write(data)
                break
            except BrokenPipeError:
                pass
        return out_bytes

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, job):
        """Some sanity cheking for setting a source

        Arguments:
            job {BaseJob} -- Job to add as source

        Raises:
            RuntimeError: When error occures
        """
        if self.SOURCE_JOBS and type(job) not in self.SOURCE_JOBS:
            raise RuntimeError(
                f"Given source job is not listed in SOURCE_JOBS")
        if self._source:
            raise RuntimeError(
                f"Source of pipe {self.id} was defined multiple times.")
        if self.destination is job:
            raise RuntimeError(
                f"PIPE {self.id}: You can't loop back pipes to same job ({job}).")
        self._source = job

    @property
    def destination(self):
        return self._destination

    @destination.setter
    def destination(self, job):
        """Some sanity checking for setting a destination

        Arguments:
            job {BaseJob} -- Job to add as destination

        Raises:
            RuntimeError: When error occures
        """
        if self.DESTINATION_JOBS and type(job) not in self.DESTINATION_JOBS:
            raise RuntimeError(
                f"Given destination job is not listed in DESTINATION_JOBS")
        if self._destination:
            raise RuntimeError(
                f"Destination of pipe {self.id} was defined multiple times.")
        if self.source is job:
            raise RuntimeError(
                f"PIPE {self.id}: You can't loop back pipes to same job ({job}).")
        self._destination = job

    def complete(self):
        """Checks if both source and destination are set.
        """
        return (self._source and self._destination)

    def __getstate__(self):
        """Defines behavior when a object is pickled.
        E.g. removed unpickleable attributes from object.

        Returns:
            dict -- Represents the state of the object
        """
        state = self.__dict__.copy()

        del state["SOURCE_JOBS"]
        del state["DESTINATION_JOBS"]

        try:
            state["_source"] = state["_source"].allocated.ip
            state["_destination"] = state["_destination"].allocated.ip
        except AttributeError:
            pass

        return state

    def __setstate__(self, state):
        """Takes the output of __getstate__ to
        restore an objects state.

        Arguments:
            state {dict} -- The state which should be restored
        """
        self.__dict__.update(state)

    def __str__(self):
        return f"{type(self).__name__} ID {self.id}"

    def __repr__(self):
        return str(self)


class BaseNode(NodeAllocate):

    GROUPS = "ALL"

    def __new__(cls, host='', *args, **kwargs):
        # return existing job if id is given and exists
        if host:
            if host in NODES.keys():
                return NODES[host]
            else:
                new_node = super().__new__(cls)

                new_node.active = False
                new_node._info = []

                new_node.max_jobs = 0

                new_node.jobs = []
                new_node.pre_copied = False

                NODES[host] = new_node

                return new_node
        else:
            return super().__new__(cls)

    def __init__(self, host, port=None, cpus=0, depends=[], setup_args=(), name=''):
        """Represents a Node in the network. Inherits from dispy.NodeAllocate and therefore 
        may be directly passed to a dispy.JobCluster as a node.
        This class caches its object in the module variable NODES.
        Therefore calls with the same host result in the exact same object!
        To clear the cache call the function 'reset' of the 'fission.core.base'.
        This will clear the cache for all Nodes, Jobs, Pipes and Groups.

        Arguments:
            host {str} -- IP address of the node

        Keyword Arguments:
            name {str} -- A display name (default: {''})
            For the rest see http://dispy.sourceforge.net/dispy.html#nodeallocate.
        """
        super().__init__(host, port=port, cpus=cpus, depends=depends, setup_args=setup_args)

        self._name = name

        self.GROUPS = self.GROUPS
        self.ip = self.ip_addr
        self.mac = None
        self._routing_table = []
        self._info = [[0, 0, 0, 0]]
        self._avg_info = {"cpu": None, "memory": None,
                          "disk": None, "swap": None}

    def add_job(self, job):
        """Add a Job to the node.
        The Node allocates itself to the Job.

        Arguments:
            job {BaseJob} -- Job you wish to add to the Node

        Raises:
            RuntimeError: If Job is not an instance of BaseJob or max job capacity is reached.
        """
        if not isinstance(job, BaseJob):
            raise RuntimeError(f"Tried adding {type(job)} as job to a node.")
        if len(self.jobs) < self.max_jobs:
            job.allocate(self)
            self.jobs.append(job)
        else:
            raise RuntimeError(
                f"Max job capacity of {repr(self)} reached. Can't assign new jobs.")

    def add_jobs(self, jobs):
        """Calls 'add_job' onto a list of Jobs.

        Arguments:
            jobs {list} -- A list of Jobs you wish to add.
        """
        for j in jobs:
            self.add_job(j)

    def open(self):
        """Is called by callback when Node is discovered by dispy
        Set Node active to True. And collects the MAC Address.
        """
        self.active = True
        self.mac = self.get_mac()

    def close(self):
        """Is called by callback when Node closes.
        Sets active to False and removes all that have not been finished.
        """
        self.active = False
        return self.flush()

    def flush(self):
        """Flush all jobs and return them

        Returns:
            list -- list of flushed jobs
        """
        flushed_jobs = []
        while self.jobs:
            job = self.jobs.pop()
            job.deallocate()
            flushed_jobs.append(job)

        return flushed_jobs

    def get_mac(self):
        """Gets the MAC_ADDR of the Node with its IP_ADDR in the ad-hoc network.
        """
        logger.info("Collecting mac addresses.")
        os.system(f'arp -D {self.ip} 1> mac.txt 2>/dev/null')

        #regular expressions
        mac = re.compile(r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', re.IGNORECASE)
        ip = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        
        #read file for valid information
        for line in open('mac.txt', 'r'):
            if re.findall(ip, line) == self.ip:
                return re.findall(mac, line)[0]
        return None

    def batman_info(self):
        """
        Function for data "getting" from current bat.txt file. 

        Stores data in Node._routing_table as dict({"mac" : "MAC_ADDR", "TQ": TRANSMIT_QUALITY}

        Returns:
            None -- if function throws an Error
            1    -- if function runs correctly
        """
        try:
            # regular expressions
            star = re.compile(r'\*')
            mac = re.compile(
                r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', re.IGNORECASE)
            tq = re.compile(r'(?<=\().*?(?=\))')
            last_seen = re.compile(r'[0-9]{1,3}.[0-9]{3}')
            error = re.compile(r'Error')

            self.routing_table = [] #reset routing_table
            #read file for valid information
            for line in open('bat.txt', 'r'):
                if re.findall(error, line):
                    raise FileNotFoundError
                temp = {}
                if re.findall(star, line) and (float(re.findall(last_seen, line)[0]) < 1):
                    temp = {"mac": re.findall(mac, line)[0]}
                    temp["TQ"] = re.findall(tq, line)[0]
                    self.routing_table = temp
            if self._routing_table == []:
                raise FileNotFoundError
        except FileNotFoundError:
            self._routing_table = [{"mac": None, "TQ": 255}]
            logger.debug("Batman information file doesnt exist.")

    @property
    def routing_table(self):
        return self._routing_table

    @routing_table.setter
    def routing_table(self, entry):
        """
        Adds an entry to the routing table of the Node.

        Arguments:
            entry -- {"mac": "Mac_Address", "TQ" : TRANSMIT_QUALITY] or {"mac": None, "TQ": 255} or []
        """
        #check if entry is a dict, or if empty list reset routing_table
        if not isinstance(entry, dict):
            if entry == []:
                self._routing_table = []
                return
            else:
                raise TypeError(f"Entries in routing table must be type dict.")
        #check for a valid dict
        for key in entry:
            if key == "mac" or key == "TQ":
                continue
            else:
                raise KeyError(
                    "Routing entry dicts must have Keys: 'mac' and 'TQ'")
        self._routing_table.append(entry)

    @property
    def info(self):
        return self._avg_info

    @info.setter
    def info(self, values):
        """
        Adding new values and recalculate average over last 30 values

        Saves average in node._avg_info = {"cpu" : AVG, "memory " : AVG, "disk": AVG, "swap": AVG}

        Arguments:
            values {list} -- new values of node status([cpu, memory, disk, swap])
        """
        average_time = 30  #average time period in ms

        #check if entry values are allowed
        if not isinstance(values, list):
            raise TypeError(
                f"Given parameter {values} is not an Object from type List.")
        if len(values) != 4:
            raise RuntimeError(
                f"Given list of values = {values} must contain exactly 4 entries.")
        if not all([isinstance(x, numbers.Number) for x in values]):
            raise AttributeError(f"All values in {values} must be Numbers.")

        #only append, or delete, append and recalculate sum
        if len(self._info) < (average_time + 1):
            self._info.append(values)
        else:
            self._info[0] = [(x - y)
                             for x, y in zip(self._info[0], self._info[1])]
            del self._info[1]
            self._info.append(values)
        self._info[0] = [(x + y) for x, y in zip(self._info[0], values)]

        #calculate average
        for i, j in zip(self._avg_info, range(4)):
            self._avg_info[i] = self._info[0][j]/(len(self._info)-1)

    @property
    def name(self):
        if self._name:
            return self._name
        else:
            return self.ip

    def allocate(self, cluster, ip_addr, name, cpus, avail_info=None, platform=''):
        """Needed by dispy.AllocateNode
        """
        if self.max_jobs > cpus:
            self.flush()
            logger.warning(
                f"{self} had to many preassigned jobs and was flushed. "
                "Preassigned nodes are caused by loading XML files."
            )
        self.max_jobs = cpus
        return super().allocate(cluster, ip_addr, name, cpus, avail_info=avail_info, platform=platform)

    def full(self):
        """Returns whether maximum Job capacity is reached.
        """
        return bool(len(self.jobs) == self.max_jobs)

    def __getstate__(self):
        """Defines behavior when a object is pickled.
        E.g. removed unpickleable attributes from object.

        Returns:
            dict -- Represents the state of the object
        """
        state = {'ip': self.ip, 'max_jobs': self.max_jobs}

        return state

    def __setstate__(self, state):
        """Takes the output of __getstate__ to
        restore an objects state.

        Arguments:
            state {dict} -- The state which should be restored
        """
        self.__dict__.update(state)

    def __str__(self):
        return f"Node: {self.name} with:\n" + "\n".join([f"\t{j}" for j in self.jobs])

    def __repr__(self):
        return f"Node {self.name} with {len(self.jobs)} jobs"


class BaseGroup():
    def __new__(cls, name=None, *args, **kwargs):
        if name:
            if name in GROUPS.keys():
                return GROUPS[name]
            else:
                new_group = super().__new__(cls)
                new_group.jobs = []
                new_group.nodes = []

                GROUPS[name] = new_group
                return new_group
        else:
            return super().__new__(cls)

    def __init__(self, name, *args, **kwargs):
        """Represents a Group of nodes and jobs.
        This class caches its object in the module variable GROUPS.
        Therefore calls with the same name result in the exact 
        same object! To clear the cache call the function 'reset' of the
        'fission.core.base'. This will clear the cache for all 
        Nodes, Jobs, Pipes and Groups.  

        Arguments:
            name {str} -- The name of the group
        """
        self.name = name

    def add_job(self, job):
        """Add a Job to the Group

        Arguments:
            job {BaseJob} -- The Job you wish to add

        Raises:
            TypeError: When types missmatch
        """
        if isinstance(job, BaseJob):
            if isinstance(job.GROUPS, list):
                for i, group in enumerate(job.GROUPS):
                    if isinstance(group, str) and group == self.name:
                        job.GROUPS[i] = self
            elif isinstance(job.GROUPS, str):
                job.GROUPS = [self]
            else:
                raise TypeError(
                    f"GROUPS of {type(job)} is {type(job.GROUPS)}")

            self.jobs.append(job)
        else:
            raise TypeError(f"Can not add {type(job)} as job to a group.")

    def add_node(self, node):
        """Add a Node to the Group

        Arguments:
            node {BaseNode} -- The Node you wish to add

        Raises:
            TypeError: When types missmatch
        """
        if isinstance(node, BaseNode):
            if isinstance(node.GROUPS, list):
                for i, group in enumerate(node.GROUPS):
                    if isinstance(group, str) and group == self.name:
                        node.GROUPS[i] = self
            elif isinstance(node.GROUPS, str):
                node.GROUPS = [self]
            else:
                raise TypeError(
                    f"GROUPS of {type(node)} is {type(node.GROUPS)}")

            self.nodes.append(node)
        else:
            raise TypeError(f"Can not add {type(node)} as node to a group.")
