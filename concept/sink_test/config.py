from sink_test.jobs.jobs import SourceJob
from fission.core.nodes import BaseNode
from fission.core.jobs import CSVSinkJob
from fission.core.pipes import PicklePipe
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
        start_value=1,
        outputs=[
            PicklePipe(1),
        ]
    ),
    SourceJob(
        start_value=15,
        outputs=[
            PicklePipe(2),
        ]
    ),
    SourceJob(
        start_value=219,
        outputs=[
            PicklePipe(3),
        ]
    ),
    CSVSinkJob(
        path="test.csv",
        inputs=[
            PicklePipe(1),
            PicklePipe(2),
            PicklePipe(3),
        ]
    )
]

# a list of nodes (instance of BaseNode or subclass or path of csv file)
NODES = [
    BaseNode("192.168.4.3"),
    BaseNode("192.168.4.2"),
    BaseNode("192.168.4.4"),
]
