# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import CSVSinkJob
from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from example_1.jobs.jobs import SourceJob, MiddleJob


# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "DEBUG"
LOG_FILE = "FISSION.log"

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = "192.168.0.31"

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = True

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
JOBS = [
    SourceJob(
        outputs=[
            PicklePipe(1),
        ]
    ),
    MiddleJob(
        inputs=[
            PicklePipe(1),
        ],
        outputs=[
            PicklePipe(2),
        ]
    ),
    CSVSinkJob(
        path="test.csv",
        inputs=[
            PicklePipe(2),
        ]
    )
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.0.30"),
    BaseNode("192.168.0.28"),
    BaseNode("192.168.0.29"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
