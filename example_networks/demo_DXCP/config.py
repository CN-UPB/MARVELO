# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from demo_DXCP.jobs.jobs import read_data, dxcp_phat, print_results
from shared.jobs.jobs import LoggingSinkJob

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
		samples_per_packet=2048,
		soundfile_path = "/home/konrad/marvelo-demo/examples/demo_DXCP/signal_file.wav",
		outputs=[
			PicklePipe(1),
			PicklePipe(2),
		],
		logging_output = PicklePipe(11),
		name = "read_data"
	),
	dxcp_phat(
		inputs=[
			PicklePipe(1),
			PicklePipe(2),
		],
		outputs=[
			PicklePipe(3),
			PicklePipe(4),
		],
		logging_output = PicklePipe(12),
		name = "dxcp_phat"
	),
	print_results(
		inputs=[
			PicklePipe(3),
			PicklePipe(4),
		],
		logging_output = PicklePipe(13),
		name = "print_results"
	),
	LoggingSinkJob(
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
