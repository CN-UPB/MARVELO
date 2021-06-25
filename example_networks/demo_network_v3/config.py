# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.pipes import PicklePipe
from fission.core.nodes import BaseNode
from fission.core.jobs import CSVSinkJob

from shared.jobs.jobs import SourceJob
from demo_network_v3.jobs.jobs import ReduceJob, JoinJob
from demo_network_v3.pipes.pipes import ReducePipe

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
# This can be an instance of BaseJob or any of its subclasses.
JOBS = [
    SourceJob(
        outputs=[
            PicklePipe(101),
            PicklePipe(201),
        ]
    ),
    SourceJob(
        outputs=[
            PicklePipe(102),
            PicklePipe(202),
        ]
    ),
    SourceJob(
        outputs=[
            PicklePipe(103),
            PicklePipe(203),
        ]
    ),
    JoinJob(
        inputs=[
            PicklePipe(101),
            PicklePipe(102),
            PicklePipe(103),
        ],
        outputs=[
            ReducePipe(105),
            PicklePipe(205),
        ]
    ),
    ReduceJob(
        inputs=[
            ReducePipe(105),
        ],
        outputs=[
            PicklePipe(301),
        ]
    ),
    CSVSinkJob(
        path="join.csv",
        inputs=[
            PicklePipe(201),
            PicklePipe(202),
            PicklePipe(203),
            PicklePipe(205),
        ]
    ),
    CSVSinkJob(
        path="reduce.csv",
        inputs=[
            PicklePipe(301),
        ]
    ),
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.4.2"),
    BaseNode("192.168.4.3"),
    BaseNode("192.168.4.4"),
]

# Whether or not files (dependencies) for every job should be copied
# to every node. If not files will be copied before the job starts.
# Turning it on results in higher setup time when starting the network
# but reduces the delay in case of failover. It also demands more disk
# space on the nodes.
PRE_COPY = False

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific use cases 
XML_FILE = None
