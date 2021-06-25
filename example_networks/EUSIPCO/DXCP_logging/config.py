# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import CSVSinkJob
from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from DXCP_logging.jobs.jobs import read_data, dxcp_phat, print_results
from shared.jobs.jobs import CSVSinkJob_2

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
	read_data(
		samples_per_packet=[32,64,128,256,512,1024,2048],
		outputs=[
			PicklePipe(1),
			PicklePipe(2),
			PicklePipe(11),
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
			PicklePipe(5),
			PicklePipe(12),
		],
	),
	print_results(
		inputs=[
			PicklePipe(3),
			PicklePipe(4),
			PicklePipe(5)
		],
		outputs=[
			PicklePipe(13),
			]
	),
	CSVSinkJob_2(
		path="dxcp_logging.csv",
		inputs=[
			PicklePipe(11),
			PicklePipe(12),
			PicklePipe(13),
			]
		)
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
	BaseNode("192.168.0.30"),
	BaseNode("192.168.0.29"),
	BaseNode("192.168.0.28"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
