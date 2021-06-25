# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import InteractiveJob, CSVSinkJob
from fission.core.nodes import BaseNode
from fission.core.pipes import PicklePipe

from example_4.jobs.jobs import MiddleJob, HeadJob
from example_4.pipes.pipes import InteractivePipe

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
    InteractiveJob(
        outputs=[
            PicklePipe(1)
        ]
    ),
    InteractiveJob(
        outputs=[
            PicklePipe(2)
        ]
    ),
    MiddleJob(
        inputs=[
            PicklePipe(1),
            PicklePipe(2),
        ],
        outputs=[
            PicklePipe(3)
        ]
    ),
    HeadJob(
        inputs=[
            PicklePipe(3)
        ],
        outputs=[
            PicklePipe(4)
        ]
    ),
    CSVSinkJob(
        path = 'test.csv',
        inputs=[
            PicklePipe(4)
        ]
    )

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

# Whether or not files (dependencies) for every job should be copied
# to every node. If not files will be copied before the job starts.
# Turning it on results in higher setup time when starting the network
# but reduces the delay in case of failover. It also demands more disk
# space on the nodes.
PRE_COPY = False

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
