from some_network.jobs.jobs import SumJob, SourceJob
from some_network.pipes.pipes import IntPipe
from fission.core.jobs import DynamicMARVELOJob
from fission.core.nodes import MultiNode
from fission.core.pipes import PicklePipe, JSONPipe
# import multiprocessing

# multiprocessing.set_start_method('spawn', True)

USER = "pi"

REMOTE_ROOT = f"/home/{USER}/fission/"

XML_FILE = None

# Logging
LOG_LEVEL = "DEBUG"
LOG_FILE = "FISSION.log"

DEBUG_WINDOW = True

CLIENT_IP = "192.168.4.1"

# a list of jobs (instance of BaseJob or subclass or path of csv file)
JOBS = [
    SourceJob(
        outputs=[
            PicklePipe(1),
            PicklePipe(2),
        ]
    ),
    SumJob(
        inputs=[
            PicklePipe(1),
        ]
    ),
    SumJob(
        inputs=[
            PicklePipe(2),
        ]
    ),
    # DynamicMARVELOJob(
    #     dependencies="some_network/source/sumjob",
    #     executable="python3 sum.py",
    #     inputs=[
    #         IntPipe(3),
    #     ]
    # )
]

PRE_COPY = False

# a list of nodes (instance of BaseNode or subclass or path of csv file)
NODES = [
    MultiNode("192.168.4.*"),
]
