# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import DynamicMARVELOJob
from fission.core.nodes import BaseNode
from fission.core.pipes import BytesPipe
from CDR.jobs.jobs import Spark3Job
from CDR.nodes.nodes import Spark3Node

# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "DEBUG"
LOG_FILE = "FISSION.log"

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = "192.168.4.1"

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = True

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
SPARK_BYTES = 4*4*12
SPARK_UPFRAME = 3

JOBS = [
    Spark3Job(
        outputs=[
            BytesPipe(11, block_size=SPARK_BYTES)
        ],
        param="config/asnupb6/Audio2Pipe4Channels.scf"
    ),
    Spark3Job(
        inputs=[
            BytesPipe(11, block_size=SPARK_BYTES)
        ],
        outputs=[
            BytesPipe(1, block_size=SPARK_BYTES*SPARK_UPFRAME)
        ],
        param="config/framing/frame128to384_c4.scf"
    ),
    DynamicMARVELOJob(
        dependencies="source/CDR/2",
        executable="./module_power_spectra_estimator.py",
        parameters="-fl 24. -noc 4 --minimumfrequency 125.0 --maximumfrequency 3500.0",
        inputs=[
            BytesPipe(1, block_size=SPARK_BYTES*SPARK_UPFRAME)
        ],
        outputs=[
            BytesPipe(2, block_size=)
        ]
    ),
    DynamicMARVELOJob(
        dependencies="source/CDR/3",
        executable="./module_signal_coherence_estimator.py",
        parameters="-noc 4 -cc 0-1,0-2,0-3,1-2,1-3,2-3 --minimumfrequency 125.0 --maximumfrequency 3500.0",
        inputs=[
            BytesPipe(2, block_size=)
        ],
        outputs=[
            BytesPipe(3, block_size=)
        ]
    ),
    DynamicMARVELOJob(
        dependencies="source/CDR/4",
        executable="./module_cdr_estimator.py",
        parameters="-noc 4 -cc 0-1,0-2,0-3,1-2,1-3,2-3 --minimumfrequency 125.0 --maximumfrequency 3500.0 sensor_positions_4.csv",
        inputs=[
            BytesPipe(3, block_size=)
        ],
        outputs=[
            BytesPipe(4, block_size=)
        ]
    ),
    DynamicMARVELOJob(
        dependencies="source/CDR/5",
        executable="./module_diffuseness_estimator.py",
        parameters="-fs 8.0 -sf 16000 -cc 0-1,0-2,0-3,1-2,1-3,2-3",
        inputs=[
            BytesPipe(4, block_size=)
        ]
    )
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.4.2"),
    BaseNode("192.168.4.3"),
    BaseNode("192.168.4.4"),
    Spark3Node("192.168.4.5"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
