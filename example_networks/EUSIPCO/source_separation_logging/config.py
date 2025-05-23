# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import CSVSinkJob
from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from source_separation_logging.jobs.jobs import ica_readModule, cov1svd, cov1svd_sqrtfn, cov2svd, sqrtfn, whiten, normfn, CSVSinkJob_2
from source_separation_logging.nodes.nodes import CoreNode, SourceNode
from shared.jobs.jobs import ForwardingJob


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
	ica_readModule(
		"/home/pi/afdwc/examples/source_separation/mix1.wav",
		outputs=[
			PicklePipe(1),
			PicklePipe(11),
		]
	),
	ica_readModule(
		"/home/pi/afdwc/examples/source_separation/mix2.wav",
		outputs=[
			PicklePipe(2),
			PicklePipe(12),
		]
	),
#    ForwardingJob(
#        inputs=[
#            PicklePipe(1),
#            PicklePipe(2)
#            ],
#        outputs=[
#			PicklePipe(21),
#			PicklePipe(22),
#		],
#    ),
	cov1svd_sqrtfn(
		inputs=[
			PicklePipe(1),
			PicklePipe(2),
		],
		outputs=[
			PicklePipe(3),
			PicklePipe(4),
			PicklePipe(5),
			PicklePipe(13),
		],
	),
#	sqrtfn(
#		inputs=[
#			PicklePipe(3),
#		],
#		outputs=[
#			PicklePipe(6),
#			PicklePipe(14),
#		],
#	),
	whiten(
		inputs=[
			PicklePipe(3),
			PicklePipe(4),
			PicklePipe(5),
		],
		outputs=[
			PicklePipe(7),
			PicklePipe(9),
			PicklePipe(15),
		],
	),
	normfn(
		inputs=[
			PicklePipe(7),
		],
		outputs=[
			PicklePipe(8),
			PicklePipe(16),
		],
	),
	cov2svd(
		inputs=[
			PicklePipe(8),
			PicklePipe(9),
		],
		outputs=[
			PicklePipe(17),
			],
	),
	CSVSinkJob_2(
		path="file.csv",
		inputs=[
			PicklePipe(11),
			PicklePipe(12),
			PicklePipe(13),
			#PicklePipe(14),
			PicklePipe(15),
			PicklePipe(16),
			PicklePipe(17),
		],
		
	),
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
	BaseNode("192.168.0.30"),
	BaseNode("192.168.0.29"),
	SourceNode("192.168.0.28"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
