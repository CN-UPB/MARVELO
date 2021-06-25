# Set the Configuration

This is a plain config file:

```python
# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

# Enter the user on the remote machines
USER = "pi"

# The directory all the action is done on the remote machines
REMOTE_ROOT = f"/home/{USER}/fission/"

# Logging
LOG_LEVEL = "DEBUG"
LOG_FILE = "FISSION.log"

# Enter the clients ip within the network, must be visible for nodes
CLIENT_IP = "192.168.0.31"

# Debug window
# Redirects stdout to console
DEBUG_WINDOW = True

# A list of jobs to be executed within the network.
# This can be an instance of BaseJob or any of its subclasses
# or a path to csv file defining jobs (see documentation).
JOBS = [ ]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [ ]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
```

Most of the lines are self explanatory. 

Set `USER` to the username of your nodes. All nodes must have the same.

`REMOTE_ROOT` is the working directory on your servers.

`LOG_LEVEL` can be `"INFO"` for the important logs or `"DEBUG"` for detailed information. Set the name of the log file with `LOG_FILE`.

Insert the client's IP address in `CLIENT_IP` and set `DEBUG_WINDOW` to `True` if you want all standard outputs from your servers at you client's console.

You can define you network topology and nodes either with declaring the jobs/nodes directly in this file or load a XML-file.

When you want to define the jobs directly in the config file, initialize them in the `JOBS` list. An element of this list looks like this:

```python
<job>(
	inputs=[
		<pipe>(<id>),
		...
	],
	outputs=[
		<pipe>(<id>),
		...
	],
	args
)
```
Actually you are doing here a normal object initialization. To know which arguments have to be set look at the `__init__` function of that job.
`inputs` and `outputs` are the lists of pipes. The order of input pipes is the same as the arguments in the run method, the order of the output pipes is the same as the return values.
You connect an input and output pipe by assigning them the same Id.
To see which pipes and jobs are already predefined look at [Implementing Pipes/Predefined Pipes](implementing_pipes) and [Implementing Jobs/Predefined Jobs](implementing_jobs).

The `NODES` list is a list of all servers of your network. An element looks like this:
```python
<node>("<ip-address>")
```
To see which nodes are already predefined look at [Implementing Nodes/Predefined Nodes](implementing_nodes).

### Use a XML file

Coming soon
