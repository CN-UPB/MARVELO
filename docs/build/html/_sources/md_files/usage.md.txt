# How to use MARVELO

## A First Example

```mermaid
graph LR
  SourceJob(SourceJob) -->|PicklePipe 1| MiddleJob(MiddleJob)
  MiddleJob(MiddleJob) -->|PicklePipe 2| CSVSinkJob(CSVSinkJob)
```

In this section we have a closer look on the first example of MARVELO.
The figure shows the network topology.
*SourceJob* generates numbers and sends them to  *MiddleJob*, which then forwards them to *CSVSinkJob*.
The last job writes everything it receives in a csv file.
For communication between the jobs, we use *PicklePipe*s, which are probalby the most versatile pipes in MARVELO.
Every datatype, you put in that kind of pipe, will come out of it.

We start by changing our working directory to `example_networks` and simulate the network by running following command

```bash 
python3 manage.py example_1 simulate
```

The console output will look somthing like this:

```bash
... 
SourceJob: 0
MiddleJob: 0
SourceJob: 1
MiddleJob: 1
SourceJob: 2
MiddleJob: 2
SourceJob: 3
MiddleJob: 3
SourceJob: 4
MiddleJob: 4
...
```

The *SourceJob* prints the number it is generating and the *MiddleJob* prints the number it is receiving.

Let us now look at the implementation of the jobs.


### How to write your first Job

Open `example_1/jobs/jobs.py`.

#### SourceJob

The code of the first job looks like following:

```python
class SourceJob(PythonJob):
    def run(self):
        value = 0
        while True:
            print(f"SourceJob: {value}")
            yield tuple([value])
            time.sleep(1)
            value += 1 
```

In the *run* method the algorithm of the job is implemented. 
In an infinite loop the job increases a counter and returns it value using `yield tuple([value])`.
Returning the value hands it over to the output pipe of the job.
Because this *run* method has no input argument, it is executed with the start of the network.


#### MiddleJob

The code of the second job looks like the following:

```python
class MiddleJob(PythonJob):
    def run(self, value):
        print(f"MiddleJob: {value}")
        return tuple([value])
```

The *run* method of this job has an argument *value*.
Whenever the input pipe of that job has a new datum, the run method is executed with this datum as the argument.
The *MiddleJob* just prints the value and returns it, so that *value* is handed over to the job's output pipe.

#### CSVSinkJob

Everything this job receives, will be written done in a csv file. This is a *LocalJob*, which means that it is always executed on the client node of the cluster.

*CSVSinkJob* is a predefined job. Therefore, we will not discuss it here further.
If there is nevertheless more interest you can find it in the [Documentation](../fission/fission.core).

### How to configure your first Network 

The configuration file is stored in `example_1/config.py` and looks like this:

```python
# ----------------------------------------------------
# FISSION CONFIG FILE
# ----------------------------------------------------

from fission.core.jobs import CSVSinkJob
from fission.core.nodes import BaseNode, MultiNode
from fission.core.pipes import PicklePipe

from example_1.jobs.jobs import SourceJob, MiddleJob


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
JOBS = [
    SourceJob(
        outputs=[
            PicklePipe(1),
        ]
    ),
    MiddleJob(
        inputs=[
            PicklePipe(1),
        ],
        outputs=[
            PicklePipe(2),
        ]
    ),
    CSVSinkJob(
        path="test.csv",
        inputs=[
            PicklePipe(2),
        ]
    )
]

# A list of nodes to be included in the network
# This can be an instance of BaseNode or Multinode
# or a path to csv file defining nodes (see documentation)
NODES = [
    BaseNode("192.168.0.30"),
    BaseNode("192.168.0.28"),
    BaseNode("192.168.0.29"),
]

# Optional XML file defining the whole network or a part of it 
# This is not recommended and only exists for specific usecases 
XML_FILE = None
```
 
Thanks to the comments the config file is pretty self explanatory. We start to imnport all the modules we are using: SourceJob, MiddleJob, CSVSinkJob, PicklePipe and BaseNode.

We set the user name of our nodes. All nodes must have the same user name. We set the name of the directory we are operating on in the remote nodes.

We can set the log configurations. Set it to `"INFO"` for general information or to `"DEBUG"` for more detailed logging.

We have to set the IP address of the client node and if we want to hava a debug window. If you choose `True` you will get all stdout from your client and servers in your console.

Now we get to the interest part of the config file: the definition of the job topology.
You add every job you want to have in your network in the `JOBS` list and initialize them. You set the inputs and outputs by adding pipes to the corresponding lists. The order in that list is the same order as in the arguments or respectivley of the return values of the run method of that job. You connect a input pipe with an output pipe by using the same ID in both declarations.
In this example we are using `PicklePipe`s, which means that every datastructure you put in will come out following the pickle protocol.
Here you also can set arguments like `path` in `CSVSinkJob`.

The `NODES` list contains an object of every node we have in the cluster. We are choosing `BaseNode` because we dont have any requirements on the nodes where we are running the jobs on. The nodes' arguments are the IP addresses of that nodes.

You can optionally set an XML file, where the whole network is defined in. Since we have defined the network with the `JOBS` and `NODES` lists, we don't have to use that. 

Now we can simulate and run our network.


## Commands

Every command for MARVELO has to look like this: 
```bash 
python3 manage.py <network_name> <command>
```
The network_name should be the name of the network you would like to work with. 
**NOTE:** When you run a MARVELO command be sure that your current working directory is the same, in which the *manage.py* file is stored. Otherwise there will probably occur problems using some commands.


### Simulating a Network

After implementing a network you should simulate it to test if it is working. Run the following command.

```bash 
python3 manage.py <network_name> simulate
```

When your jobs create output files you can find them in the directory *<network_name>/simulation/*.
The simulation can be stopped by using `CTRL+C`.

### Runnning a Network

When you want to distribute the jobs of your network, as in the config file described, and run them, use the following command.

```bash 
python3 manage.py <network_name> run
```

The console will show all active nodes in a table. If some nodes are not shown, it is a good idea to restart the MARVELO service on these nodes with
```bash
sudo service fission restart
```

When the distribution of jobs is successful, there will be a list of which node is running which job and an additional window will open, where the jobs' outputs will be shown.

The execution can be stopped by using `CTRL+C`.


### Other Commands

Here comes a list with all commands for MARVELO:
* `run`: To run the network on the given Nodes
* `simulate`: To simulate the network in subprocesses
* `startnetwork`: To start a new network, make a folder with a job, pipe, node and config file to configure the network
* `graphviz`: To make and show a pdf of the network with graphviz
* `show`: To make and show a pdf of the network with matplotlib
* `interactive`: Start a interactive Python console with the network loaded.
* `collect`: To collect all logger files from the nodes given in the *`config.py`* file on the client. The copies are stored in the network directory under *`collection`*
