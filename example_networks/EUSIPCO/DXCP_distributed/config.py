# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import CSVSinkJob
from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from DXCP_distributed.jobs.jobs import read_data, dxcp_phat, print_results
from source_separation_logging.jobs.jobs import CSVSinkJob_2
from shared.nodes.nodes import Node1, Node2, Node3, Node4
from shared.jobs.jobs import ForwardingJob, ClockJob

# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "FISSION.log"

PULSE_INTERVAL = 0.5

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = "192.168.0.31"

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = True

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
JOBS = [
	ClockJob(
        outputs=[
            PicklePipe(91),
            PicklePipe(92),
            ]
        ),
	read_data(
		channel=0,
        inputs=[
            PicklePipe(91),
            ],
		outputs=[
			PicklePipe(1),
			PicklePipe(11),
		]
	),
	read_data(
		channel=1,
        inputs=[
            PicklePipe(92),
            ],
		outputs=[
			PicklePipe(2),
			PicklePipe(12),
		]
    ),
	dxcp_phat(
		inputs=[
			PicklePipe(1),
			PicklePipe(2),
		],
		outputs=[
			PicklePipe(3),
			PicklePipe(4),
			PicklePipe(13),
		],
	),
	print_results(
		inputs=[
			PicklePipe(3),
			PicklePipe(4),
		],
		outputs=[
			PicklePipe(14),
			]
	),
	CSVSinkJob_2(
		path="file.csv",
		inputs=[
			PicklePipe(11),
			PicklePipe(12),
			PicklePipe(13),
			PicklePipe(14),
			]
		)
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
	Node3("192.168.0.30"),
	Node2("192.168.0.29"),
	Node1("192.168.0.28"),
    Node1("192.168.0.27"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
