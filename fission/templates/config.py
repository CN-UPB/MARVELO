# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

# from fission.core.jobs import ...
# from fission.core.nodes import BaseNode, MultiNode

# Enter the user on the remote machines
USER = ""

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "FISSION.log"

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = ""

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = False

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses.
JOBS = [
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
]

# Whether or not files (dependencies) for every job should be copied
# to every node. If not files will be copied before the job starts.
# Turning it on results in higher setup time when starting the network
# but reduces the delay in case of failover. It also demands more disk
# space on the nodes.
PRE_COPY = False

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None

# Defines how often you servers send a heartbeat to the client.
# When 5 heartbeats are missed a node is presumed to be dead.
# This meas `PULSE_INTERVAL` * 5 is the time to detect a failed node.
# Must be between 0.1 and 1000
PULSE_INTERVAL = 0.1

# Defines how many bytes the head has.
# First 3 bits are reserved for FISSION
HEAD_SIZE = 1
