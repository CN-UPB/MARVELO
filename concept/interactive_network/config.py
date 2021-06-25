# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.nodes import BaseNode
from fission.core.jobs import InteractiveJob
from interactive_network.jobs.jobs import SquaredJob, DoubleJob, DiffJob
from interactive_network.pipes.pipes import StringToIntPipe

# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "DEBUG"
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
    InteractiveJob(
        outputs=[
            StringToIntPipe(1),
            StringToIntPipe(2),
            StringToIntPipe(3), 
        ]
    ),
    InteractiveJob(
        outputs=[
            StringToIntPipe(4), 
        ]
    ),
    SquaredJob(
        inputs=[
            StringToIntPipe(1)
        ]
    ),
    DoubleJob(
        inputs=[
            StringToIntPipe(2)
        ]
    ),
    DiffJob(
        inputs=[
            StringToIntPipe(3),
            StringToIntPipe(4),
        ]
    )
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.4.2"),
    BaseNode("192.168.4.3"),
    BaseNode("192.168.4.4"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
