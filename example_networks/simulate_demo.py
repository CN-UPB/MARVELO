import sys
import os
from fission.manager import execute_simulation
from importlib import import_module

args = []
network = "example_withXML"
os.environ.setdefault('FISSION_CONFIG_MODULE', f'{network}.config')

config = import_module(os.environ['FISSION_CONFIG_MODULE'])
execute_simulation(config, network, *args)