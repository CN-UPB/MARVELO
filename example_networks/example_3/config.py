# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import InteractiveJob, CSVSinkJob
from fission.core.nodes import BaseNode
from fission.core.pipes import PicklePipe
from example_3.jobs.jobs import SourceJob, MiddleJob
from example_3.pipes.pipes import InteractivePipe


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
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
JOBS = [
		SourceJob(
			outputs = [
				PicklePipe(1)
			]
			),
		SourceJob(
			outputs = [
				PicklePipe(2)
			]
		),
		InteractiveJob(
			outputs = [
				InteractivePipe(3)
			]
		),
		MiddleJob(
			inputs = [
				PicklePipe(1),
				PicklePipe(2),
				InteractivePipe(3)
			],
			outputs = [
				PicklePipe(4)
			]
		),
		CSVSinkJob(
			inputs = [
				PicklePipe(4)
			],
			path = "test.csv"
		)
	]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = []

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
