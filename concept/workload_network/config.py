# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

# from fission.core.jobs import 
from fission.core.nodes import BaseNode
# from fission.core.pipes import ArrayPipe
from workload_network.jobs.jobs import MemoryJob, SumJobMemory, WorkloadJob, SumJobWorkload
from workload_network.pipes.pipes import FloatPipe

# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "FISSION.log"

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = "192.168.4.1"

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = True

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
JOBS = [
    MemoryJob(outputs=[
        FloatPipe(1),
    ]),
    WorkloadJob(outputs=[
        FloatPipe(2),
    ]),
    SumJobMemory(inputs=[
        FloatPipe(1),
    ]),
    SumJobWorkload(inputs=[
        FloatPipe(2),
    ])
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.4.3"),
    BaseNode("192.168.4.2"),
    BaseNode("192.168.4.4"),
    BaseNode("192.168.4.5"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
