# Develop your own Network

[[_TOC_]]

## Creating a new Project

To start a **MARVELO** project just run:

```bash
fission_admin.py <my-project> startproject
```

This will result in the following structure:

```
<my-project>/
├── manage.py
└── shared
    ├── __init__.py
    ├── jobs
    │   ├── __init__.py
    │   └── jobs.py
    ├── nodes
    │   ├── __init__.py
    │   └── nodes.py
    ├── pipes
    │   ├── __init__.py
    │   └── pipes.py
    └── source
```

By default a `shared` network is started. 
It contains no `config.py` file and there for can't be directly executed.  
It's purpose is to hold jobs, nodes, pipes and files you may want to use in multiple networks within you project.

Next head into ```<my-project>``` and start a network:

```bash
cd <my-project>
python3 manage.py <my-network> startnetwork
```

The folder structure changes to:

```
<my-project>/
├── manage.py
├── shared
│   ├── __init__.py
│   ├── jobs
│   │   ├── __init__.py
│   │   └── jobs.py
│   ├── nodes
│   │   ├── __init__.py
│   │   └── nodes.py
│   ├── pipes
│   │   ├── __init__.py
│   │   └── pipes.py
│   └── source
└── <my-network>
    ├── config.py
    ├── __init__.py
    ├── jobs
    │   ├── __init__.py
    │   └── jobs.py
    ├── nodes
    │   ├── __init__.py
    │   └── nodes.py
    ├── pipes
    │   ├── __init__.py
    │   └── pipes.py
    └── source
```

Notice how our newly created network provides a `config.py` file, meaning we can actually run it.

We'll return to the config later, first a quick explanation of what's what:

- ```config.py``` is the part of your network where you define a few general things, but also how and with what pipes your jobs are connected.

- ```jobs``` is a directory / python module where you are meant to define your jobs in.

- ```nodes``` is a directory / python module where you are meant to define your nodes in.

- ```pipes``` is a directory / python module where you are meant to define, you guessed it, your pipes in.

- ```source``` is a directory where you are meant to put your job's dependencies like executables or in general files you job depends on.



## Implementing Jobs

This page covers what you need to think about when making a job for **MARVELO**.  

### Overview

In general there are 2 types of jobs:

- [Python Jobs](#python-jobs)
- [Executable Jobs](#executable-jobs)

In addition we differentiate between 3 types depending on in- and outputs:

- **Source job**: A job which only has outputs, no inputs. 
  It only feeds data into the network.
- **Connector Job**: A job providing both in- and outputs. It processes and forwards.
- **Sink Job**: A job which only has inputs. It may process data and is likely to store results somewhere.

[Python Jobs](#python-jobs) need to be implemented in Python and are therefore highly integrated into our Python based framework.  

[Executable Jobs](#executable-jobs) on the other hand allow to run any type of executable that takes the correct argument and knows how to handle them.  

### Predefined Jobs
There are some already implemented jobs that may be useful. 

#### CSVSinkJob

#### InteractiveJob


#### LoggingJob and LoggingSinkJobs


#### DataJob


#### ClockJob


#### ForwardingJob



### GROUPS, DEFAULT_NODE and MAX_QUEUE

These are class attributes of a job. You can override them.

- `GROUPS`:  
  A list of strings or a single string representing a name for a group. 
  A group is used when allocating a job. 
  Jobs will only be allocated to nodes of the same group(s).  
  When listing multiple groups, order matters. 
  First one being highest priority and last one lowest.  
  The group "ALL" is the default groups each node and job is part of, if not specified.

- `DEFAULT_NODE`:
  This is a ip address as a string. 
  Each time the job is allocated, it will try to allocate this job to the given node.
  If it isn't reachable or full it will fall back on the given `GROUPS`

- `MAX_QUEUE`(inaccurate):
  This is used to specify how many inputs will be queued before deleting old ones.  
  This isn't a exact amount as there are many pipes and queues involved but a rough orientation.  
  Using pipes with the "ASYNC" flag active will first fill up the entire named pipe before starting to count inputs and discard them.

If you were to define your own class attribute and want it to be accessible on your server nodes please note that you have to load the class attribute into the object for it to be detected by pickle:

```python
class MyJob(PythonJob):

    MY_ATTRIBUTE = "MY_VALUE"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # safe it into the object
        self.MY_ATTRIBUTE = self.MY_ATTRIBUTE

        # or rename it while saving it into the object
        self.my_attribute = self.MY_ATTRIBUTE
```

This is kind of pointless when facing variable class attributes as they won't be updated, but as we use them for constants this is fine and allows for a clearer job definition.  

### Python Jobs

Python jobs are the easiest way to implement a job for **MARVELO** and are recommended unless you have to use another language due to compatibility or performance issues/concerns.

To start developing a Python job you need to import `PythonJob` from `fission.core.jobs`. 
This is the class implementing all the boilerplate code for interacting with pipes, converting Python objects to a byte representation and few other things.  
There are two methods you are meant to override:

- `setup`
- `run`

#### Setup your job

`setup` is called once before entering a loop calling `run`.
It allows to initiate variable, open files and so on before the job starts.  

> Why don't we use `__init__` for that?

This is because `__init__` is called on the client when the jobs are instantiated. 
This means everything you define in the `__init__` needs to be send over to the node, transferring more data and maybe causing issues because some objects can't be pickled ([What can be pickled and unpickled?](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled)).  
So the `__init__` is only meant to initiate attributes you can not generate on the node such as a path to a custom file.
Always make sure you pass arguments through super() methods, a quick example:

```python
class MyJob(PythonJob):
    def __init__(self, my_path, *args, **kwargs):
        """This is executed on the client machine with the arguments
        specified in the config file.
        """
        # call the init of the super class
        super().__init__(*args, **kwargs)

        # store my custom attribute.
        # I need to define the path to this file int the config
        # as it cant be generated in `setup`
        self.my_path = my_path

    def setup(self, *args, **kwargs):
        """This is executed on the server before the job starts
        """
        # call setup from super class and pass arguments.
        super().setup(*args, **kwargs)

        # now I open the the path that was initated on the client.
        # I can access both attributes within the `run` method
        self.my_file = open(self.my_path, "r")
```

#### Implementing the actual logic

The `run` method defines the actual job being executed. 

##### Source Job

Let's start with a source job:  
Needless to say, a source job won't be passed any arguments. 
As it is likely you wish to keep context in your source job between calls of `run` it is possible for the `run` method to be a generator.
So a source job counting from 1 to 30 can be defined in two ways:  

**As a normal method**:

```python
class CountJob(PythonJob):
    HEAD = True
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.counter = 0
        self.limit = 30

    def run(self):
        self.counter += 1

        if self.counter == self.limit:
            self.finish()

        return self.counter
```

**As a generator** (no `setup` needed):

```python
class CountJob(PythonJob):
    HEAD = True
    def run(self):
        for i in range(1, 31):
            if i == 30:
                self.finish()

            yield i
```

**returning `None` will end a job without properly finishing it.**

Notice how using the generator is much easier and more compact.  
You may wonder what's up with `HEAD = True` and the `self.finish()` call. 
This will be covered in [Interacting with the MARVELO Head](#interacting-with-the-fission-head), so don't bother too much at this point.

> Okay but we returned only one value, does that mean we can only attach one output?  

No. For convenience returning a value that is not of type `tuple`, it will be distributed to all outputs defined in the config file.  
If you wish to send different values to different outputs you have to return a tuple, in the same order as the outputs defined in the config.  

If you need to return a single tuple just return a tuple containing a single tuple. If you need to map it to all outputs do

```python
my_tuple = tuple()
return tuple([(my_tuple)] * len(self.outputs))
```

Example:

```python
class CountJob(PythonJob):
    HEAD = True
    def run(self):
        for i in range(1, 31):
            if i == 30:
                self.finish()

            yield (i, 31 - i)
```

This means for the following job definition:

```python
CountJob(
    outputs=[
        SomePipe(1),
        SomePipe(2),
    ]
)
```

The job on the other end of the pipe with id 1 will receive values counting up from 1 to 30 and the one at id 2 would receive values counting from 30 down to 1.

#### Connector and Sink Jobs

Now it is all about inputs. The `run` method will never be called with key word arguments, it's all about positional arguments.  
This means you can define a fixed number of inputs, take a variable amount of inputs or make a mix of both.  

Let's make a job that takes 2 arguments and calculates the sum:

```python
class SumJob(PythonJob):
    def run(self, in_1, in_2):
        return in_1 + in_2
```

This should be self-explanatory.  
Next we will make a job that take a variable amount of inputs and calculates the sum:

```python
class SumJob(PythonJob):
    def run(self, *args):
        return sum(args)
```

At last a job taking one fixed input, a multiplier, and a variable number of inputs that will be summed up and multiplied with the multiplier:

```python
class MultiplySumJob(PythonJob):
    def run(self, multiplier, *args):
        return multiplier * sum(args)
```

This required at least two inputs, because the `sum` with an empty list raises an exception.  
Like with the outputs, the order in which the inputs are given matters:

```python
MultiplySumJob(
    inputs = [
        SomePipe(1),
        SomePipe(2),
        SomePipe(3),
    ],
    outputs = [
        SomePipe(4),
    ]
)
```

This will multiply id 1 with the sum over id 2 and 3 and forward it to id 4.

Sink jobs are basically the same thing but they have no return value.  
They can be e.g. used to store results in a file.

#### Local job

Local jobs are always executed on the client node without any dispy involved.  
These jobs are useful to collect data from the network or inject data from the client.

To mark a jobs as local just inherit from `fission.core.jobs.LocalNode`.  
If you were to change the `GROUPS` make sure you still list "LOCAL".

This will create a local version of the `MultiplySumJob`

```python
from fission.core.jobs import LocalJob

class LocalMultiplySumJob(LocalJob, MultiplySumJob):
    def run(self, multiplier, *args):
        return multiplier * sum(args)
```

#### Using modules

If you want to use modules which are installable over pip, make sure you list them in the ansible script when setting up your servers.
This allows you to just normally import them in the module you define your job in.

When you want to write a custom module for helper functions or classes and want to use them you have to:

1. List the module in the dependencies class attribute
2. Make sure you import the module relative to your projects root directory!

You may also list one directory containing files that are copied before executing the job.

Example:

```python
import mynetwork.job.mymodule as mymodule

class MyJob(PythonJob):
    DEPENDENCIES = ["a/directory/", mymodule]
    def run(self, a, b):
        # I need mymodule and the files from "a/directory" to work.
```

If you use the `PicklePipe` and directly send custom Python objects over it, make sure both the sending and receiving job have the according module listed!

#### MARVELO Head interface

If you set the class attribute `HEAD` to `True` you are able to interact with the MARVELO head.

To make it as easy as possible we created a class `Head` each Head is converted to.
This class allows you to easily interact bitwise via indexing, without the need of implementing bitwise operations.

Below you can see a list, which bitwise operations can be performed on a head in a class `Head`

- `and`
- `or`
- `xor`
- `left-shift`
- `right-shift`
- `inverting`
- `indexing`
- `slicing`
- `Setting a bit`

The first three operations `and`, `or`, `xor`  are performed with another Head-object or an integer

The both `shift` operations can be only performed with another integer.

The `inverting` operation, as the just name suggests, just inverts the head.

With `indexing` you are able to access an bit and you able to see if the certain bit is set, which gives a return value True, if not the return value would False.

With `slicing` your are able return some specific part of head.

Last but least, you can `set` a specitfic bit in head. It is important to say that you are not allowed to set the second bit, because it is reserved.

All these bitwise operations are returning  a Head-object, apart from indexing and setting a bit.



Within a jobs `run` method you have two heads to access:

- `self.head`: A reduced version of your head.
  By default this is the result of a bitwise `or` comparison for all heads for a given compute block.  
  By overriding the `head_reduce` method of your job you can change this behaviour.
  The return value of this method will be assigned to `self.head` before `run` is called.  
  This value will be mapped to each outgoing pipe which value has not changed.

- `self.in_heads`: A list (of lists) containing all heads as objects of `Head` in the same order as `inputs`.
  If a incoming pipe has `BLOCK_COUNT` > 1 the entry will be a list containing each head in the order they have been read (index 0 being the first).
  This can be used by `head_reduce` do define `self.head`

- `self.out_heads` is reset to a list of `None`s, the length of the number of outputs a job has, before each call.
  You may set a custom head for each outgoing pipe by changing the associated entry in `self.out_heads`.  
  Each `None` entry will be replaced with `self.head` before writing each head.

The first 3 bits are reserved by **MARVELO**, for more information see [Synchronization](fission/Synchronization.md).


### Executable Jobs

There are two kinds of Executable jobs available:

- `ExecutableJob`
- `MARVELOJob`

The only way they differ is that `ExecutableJob` will pass paths to the name pipes and `MARVELOJob` will pass file descriptors.  

You will have to accept flags for every input and every output.
These flags default to `-i` for inputs and `-o` for outputs but can be adjusted to your needs.
They will be passed in the order defined in the config file.  
Each in- or output is passed with an additional flag, so you need to resolve them in append mode.  
Opening them and reading and writing is up to you at this point.  

Be aware that you have to read **and** write the head if you set it to `True`.
This default to one byte you have to read and write before the rest of the data.

> So how do I define a ExecutableJob?

Whether you use `ExecutableJob` or `MARVELOJob` does not matter for defining it, we will stick to `ExecutableJob` for now.

```python
class MyExecutableJob(ExecutableJob):
    # The actual command being run.
    # If included in the dependencies folder
    # this should be relativ to it.
    EXECUTABLE = "./my_executable"

    # The folder containing everything the job needs to be executed.
    # We recommend the source folder of your network or the shared source folder
    # This is optional
    DEPENDENCIES = "my_network/source/my_executable_job"

    # some additional parameters does not have to be defined
    PARAMETERS = "--my_addition 2 --parameters"

    # this defaults to '-i'
    INPUT_FLAG = '--input'

    # this defaults to '-o'
    OUTPUTS_FLAG = '--output'
```

That's it. You can import this job and use it in your config.  
You could also do something like this:

```python
class MyExecutableJob(ExecutableJob):
    EXECUTABLE = "./my_executable"
    DEPENDENCIES = "my_network/source/my_executable_job"
    INPUT_FLAG = '--input'
    OUTPUTS_FLAG = '--outputs'

    def __init__(self, params='', **kwargs):
        super().__init__(**kwargs)
        self.PARAMETERS = params
```

This allows you set custom parameters in the config without having to define a new class every time.

Alternatively there is a "dynamic" variant of both `ExecutableJob` and `MARVELOJob`, called `DynamicExecutableJob` and `DynamicMARVELOJob`.

They allow you to define all these parameters without the need of creating a new class by passing them in the config file:

```python
DynamicExecutableJob(
    executable="./my_executable",
    dependencies="my_network/source/my_executable_job",
    parameters="--my_addition 2 --parameters",
    input_flag='--input',
    output_flag='--output',
    head=False,
    groups='ALL',
    ...
)
```

When using Executable jobs and combine them with Python jobs you will have to think about what exactly is send by the Executable job and how you need to convert it before passing it to a Python job's `run` method.
This also goes the other way around.

This is explained in [Creating a Pipe](Creating-a-Pipe.md).

#### MARVELO Head

If you set the `HEAD` attribute, you have to read `HEAD_SIZE` bytes before reading the actual data.  
You will also have to write the head of the same size to the output before writing any data.  
`HEAD_SIZE` defaults to 1.

The first 3 bytes are reserved by **MARVELO**, for more information see [Synchronization](fission/Synchronization.md).


## Implementing Pipes

This section covers what you need to think about when making a pipe for **MARVELO**.

### Overview

A **MARVELO** pipe is where the protocols between jobs are defined.  
There are a few powerful pipes predefined in `fission.core.pipes` which suffice most cases but you can implement you own pipes if you want to.

Introducing 2 terminologies:

- Block: Is one output to a single pipe.
- Compute block: Is a complete set of blocks a job need before it can compute something.
  Each job (excluding source jobs) needs to receive one ore multiple blocks on each input before being able to compute something.

Class attributes:

- `BLOCK_SIZE` is either a string or integer.
  If you implemented a custom protocol with variable length this should be string identifying the protocol.
- `BLOCK_COUNT` describes how many blocks are needed on this pipe until the receiving end is able to compute.
  For Python jobs this means it will pass a list of values of length `BLOCK_COUNT` instead of a single value.  
  For Executable jobs this will just write `BLOCK_COUNT` times to the pipe. This information is still needed to properly determine SQNs.
- `ASYNC` will be covered [later](#async-and-optional-pipes).
- `SOURCE_JOBS` is a list of job classes allowed as source of this pipe.
  It is not needed at any time but may be useful to avoid errors while configuring your network.
- `DESTINATION_JOBS` is a list of job classes allowed as destination of this pipe.
  It is not needed at any time but may be useful to avoid errors while configuring your network.


### Predefined Pipes

The following pipes are predefined:

- `PicklePipe`
- `JSONPipe`
- `BytesPipe`

#### PicklePipe

The PicklePipe, as the name suggests, implements a pipe using [pickle](https://docs.python.org/3/library/pickle.html) and is therefore very suitable for communicating between Python jobs without worrying about too much.
Only thing you have to worry about is to make sure you defined the dependencies correctly at both ends when sending objects from custom modules. Described [here](Create-a-Job#using-modules).

As this is Python specific, it is not suitable for communicating with any Executable job running some other language

#### JSONPipe

This pipe sends data in the JSON format it therefore is very versatile. 
It relies on sending JSON in one line with an ending line break to distinguish between multiple in-/outputs.

This does not have to bother you when using Python job. 
You just need to stick to types that are convertible according to [this table](https://docs.python.org/3/library/json.html?highlight=jsondecoder#json.JSONDecoder).
Otherwise errors will occur while converting Python objects.

#### BytesPipe

A very basic pipe allowing to specify the amount of bytes expected to be send.

It allows to to set the amount being send/received in the config:

```python
JOBS = [
    SomeJob(
        inputs=[
            BytesPipe(1, 64, 2)
        ]
    )
]
```

This example will read 64 bytes (BLOCK_SIZE) from the pipe twice (BLOCK_COUNT).

Normally you sill want to define [pack](#packdata) and [unpack](#unpackdata) methods.

### Implementing my own pipe

We highly recommend to take a look at the `fission.core.pipes` module see a few examples of pipe implementations.

There are 5 methods that are essential to a pipes behaviour:

#### Python job specific

##### `read(file_obj)`

This method take a file_obj opened in binary read mode and reads a block from it.  
It is supposed to return bytes but may also return something else if it is inefficient to read the bytes before converting it to Python objects.
E.g. the `PicklePipe` violates this rule.

##### `unpack(data)`

This method it called with what ever [read](#readfileobj) returns.  
It is supposed to return a Python object created from the bytes read in [read](#readfileobj).
The default implementation always returns `data`.  
It is meant to convert the received bytes from the network to a Python object suitable for the `run` method of the job.

##### `write(file_obj, data)`

This method is passed a file opened in binary write mode and data it is supposed to write to the file object.  
`data` is what ever [pack](#packdata) returns and should be bytes.

##### `pack(data)`

This method is meant to convert return values of the `run` method of a job into bytes to be able to send it across the network.

#### General

##### `read_wrapper(file_obj)`

This method will be similar to the [read](#readfileobj) method.
It is called in the wrapper when reading from a jobs output pipe and therefore not only effecting Python jobs but Executable jobs.
Other than [read](#readfileobj) this method **has to return bytes**.  
By default this method just calls [read](#readfileobj) and returns it return value.

> Why do we have this method?

Taking the `PicklePipe` as an example, we can't use `pickle.load` to read from a pipe because necessary modules might not be loaded in the wrapper.  
Therefore we need a method that only reads a bytes representation.
Doing so each time before converting it to Python objects would be inefficient, therefore we have two different methods.

### ASYNC and Optional Pipes

Setting the `ASYNC` flag to `True` will cause the pipe to bypass the [SQN Checker][fission/Synchronization#sqn-checker] and be directly forwarded to the underlying job.  

This is of special interest when talking about [optional pipes](fission/Data-Structure#optionalmixin).
When you have a job that produces outputs occasionally but only improves your computation and isn't necessary or will always be the same unless changed, this is what you need.

Let's say we use an `InteractiveJob` that reads user input once in a while to change a parameter of a job (see [examples](Examples#version-4)) we do not want to rely on the user to inputs this parameter as frequently as other jobs may produce data.
Therefore we want this input to be optional, have a default and it maybe should be overridden with the latest value.

All of this provides the [OptionalMixIn](fission/Data-Structure#optionalmixin).

**Only works with PythonJobs on the receiving end**

This MixIn creates a pipe which does not have to read data for each time `run` is called.  
Instead you can define a default value which should be returned by the pipe's `read` method.
If the pipe received a value, it will be returned instead.  
You may also set whether the value should be saved, and replace the default value or just should be passed once and afterwards fall back on the old default value, if no new inputs are available.  
At last you can also set a buffer size, indicating how many inputs the pipe is allowed to buffer before deleting data.

This MixIn enables the `ASYNC` flag.

This behaviour is achieved by calling `super().read()` in a thread while overriding the `read` method and having a queue between main and sub thread.
This means this MixIn can only be used to **extend a existing pipe** by having the `OptionalMixIn` before the pipe you wish to extend in the mro.

```python
class MyOptionalPipe(OptionalMixIn, MyNormalPipe):
    OPTIONAL_DEFAULT = "And now I override the class attributes"
```

**Class attributes**:

- `OPTIONAL_DEFAULT`: The default value, defaults to `None`. 
  Keep in mind that this is the value returned by `read` and therefore `unpack` will be called with it.
- `OPTIONAL_STORE`: Whether the value should be stored or not. Defaults to `True`
- `OPTIONAL_BUFFER_SIZE`: Buffer size, defaults to 0
- `OPTIONAL_DELETE_MODE`: Defines delete mode it pipes is full. Must be `'oldest'` or `'newest'`

### Pipes as bridges between Executable jobs and Python jobs

As stated in [Python job specific](#python-job-specific), there are methods only called by Python jobs.  
Still putting the effort into developing all 5 methods listed [here](#implementing-my-own-pipe) is worth it.  
On one hand you can use the pipes to easily connect Python and Executable jobs, on the other handy it is very useful for debugging and testing a Executable like described in [debugging](Debugging).


## Edit config.py

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

The `NODES` list is a list of all servers of your network. An element looks like this:
```python
<node>("<ip-address>")
```

### Use a XML file

Coming soon

## Debugging

### Simulate

You can simulate a network by running the following command:

```bash
python3 manage.py my_network simulate
```

This will run all jobs in subprocesses and use named pipes to connect them.  
This also start the wrapper, therefore the network should run just the same as it would when run on the servers.
While running it will output the stdout and stderr of each job.
Only thing being that issues with custom modules will not be detected by simulation!

If you have jobs that need specific hardware, i.e. a microphone, we recommend you replace this job with one just feeding prerecorded data from a file for simulation.

You will find a `simulation` folder in your network folder afterwards.
This will contain a folder for each job, named after its id.
To better track down the jobs there is a `info.txt` mapping ids to jobs but in general job ids are enumerated in the order they are defined in the config.

This is a great way for final validation before trying to run it on the servers and allows for way more responsive errors.

### Interactive

You can run a interactive Python console like this:

```bash
python3 manage.py my_network interactive
```

This will load the network, including all pipes and jobs, and allows to browse the data structure freely.  
Sanity checks are disabled while loading, so you network does not have to be complete, pipes can  be open ended.

These locals are passed to the console:

- `network` the loaded network.
  A instance of `fission.core.network.Network`.
- `JOBS` a dict containing all jobs.
  `{<job_id>: <obj>}`
- `PIPES` a dict containing all pipes.
  `{<pipe_id>: <obj>}`
- `NODES` a dict containing all nodes.
  `{<node_ip>: <obj>}`
- `GROUPS` a dict containing all groups.
  `{<group_name>: <obj>}`

In addition a function `emulate` is defined.
Passing a job or pipe to it will return a emulator object.
It allows you to call your pipes or jobs like normal functions.

**Emulation will not spawn a wrapper, but emulates it by calling `read_wrapper`**

#### Pipe emulation

Calling a pipe will print detailed outputs what was read and written at what stage and return a tuple containing the output at each stage.

```python
Staring Python Interactive console.
Following variables are defines: ['network', 'JOBS', 'PIPES', 'NODES', 'GROUPS', 'emulate']
Python 3.7.5 (default, Nov 20 2019, 09:21:52) 
[GCC 9.2.1 20191008] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> PIPES
{104: OperatorPipe ID 104, 101: PicklePipe ID 101, 201: PicklePipe ID 201, 102: PicklePipe ID 102, 202: PicklePipe ID 202, 103: PicklePipe ID 103, 203: PicklePipe ID 203, 105: ReducePipe ID 105, 204: PicklePipe ID 204, 205: PicklePipe ID 205, 301: PicklePipe ID 301}
>>> p = emulate(PIPES[101])
>>> p
<fission.emulate.PipeEmulator object at 0x7fa266f2d090>
>>> p(400)
Packed to: 400
Wrote to pipe.
Read in pipe.read_wrapper: b'\x80\x03M\x90\x01.'
Rewriting to pipe (not using write method of pipe)...
Read in pipe.read: 400
Unpacked to: 400
(400, b'\x80\x03M\x90\x01.', 400, 400)
>>> 
```

You may pass a integer for head in a kwarg (`head=0`)-

#### Job emulation

**Job emulation has no great support for `BLOCK_COUNT` at this point and cause unexpected but valid behaviour with optional pipes**

**Only supports `MARVELOJob`s, not `ExecutableJob`s**

The job emulator spawns a [pipe emulator](#pipe-emulation) for each in and output.  
Calling a job at this point looks equivalent to just calling a normal function:

```python
Staring Python Interactive console.
Following variables are defines: ['network', 'JOBS', 'PIPES', 'NODES', 'GROUPS', 'emulate']
Python 3.7.5 (default, Nov 20 2019, 09:21:52) 
[GCC 9.2.1 20191008] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> JOBS
{1: InteractiveJob 1, 2: SourceJob 2, 3: SourceJob 3, 4: SourceJob 4, 5: JoinJob 5, 6: ReduceJob 6, 7: CSVSinkJob 7, 8: CSVSinkJob 8}
>>> j = emulate(JOBS[5])
>>> j
<fission.emulate.JobEmulator object at 0x7f21eb4296d0>
>>> j('+', 1, 2, 3)
Putting + in OperatorPipe ID 104.
Putting 1 in PicklePipe ID 101.
Putting 2 in PicklePipe ID 102.
Putting 3 in PicklePipe ID 103.
1+2+3 = 6
Got 6 from ReducePipe ID 105.
Got 6 from PicklePipe ID 204.
Got + from PicklePipe ID 205.
[6, 6, '+']
>>> j('*', 1, 2, 3)
Putting * in OperatorPipe ID 104.
Putting 1 in PicklePipe ID 101.
Putting 2 in PicklePipe ID 102.
Putting 3 in PicklePipe ID 103.
1*2*3 = 6
Got 6 from ReducePipe ID 105.
Got 6 from PicklePipe ID 204.
Got * from PicklePipe ID 205.
[6, 6, '*']
>>> 
```

A call returns a list containing all outputs.

The given example uses an optional pipe.
Although it looks fine, if I were to change the first call to

```python
>>> j('*', 1, 2, 3)
```

it would still produce the exact same outputs, why is that?

We used a optional pipe as a input at the first position.
This causes the job to read from it first, because it is a optional pipe and we did not provide any input while creating it, the default value is used.
It causes a shift by one for any optional pipe listed before a normal pipe.

### Debugging console

When setting the `DEBUG_WINDOW` option in the config file, a console will automatically open printing all stdout and stderr of the jobs running on you network.
This can be very crowded when running a big network with many jobs.

Therefore you can additionally launch a console only monitoring specific jobs.
When the general console is launched you will find 'Network Information' at the very beginning (and every time the network rearranges due to failover).
You will find a ip and port for each job.

```python
Network Information:
[{'ip': '192.168.4.1', 'name': 'InteractiveJob 1', 'port': 1998},
 {'ip': '192.168.4.2', 'name': 'SourceJob 2', 'port': 1996},
 {'ip': '192.168.4.4', 'name': 'SourceJob 3', 'port': 1994},
 {'ip': '192.168.4.4', 'name': 'SourceJob 4', 'port': 1992},
 {'ip': '192.168.4.4', 'name': 'JoinJob 5', 'port': 1990},
 {'ip': '192.168.4.4', 'name': 'ReduceJob 6', 'port': 1988},
 {'ip': '192.168.4.1', 'name': 'CSVSinkJob 7', 'port': 1986},
 {'ip': '192.168.4.1', 'name': 'CSVSinkJob 8', 'port': 1984}]
```

Just pick the ones you wish to monitor in a new console and execute:

```bash
fission_debug.py --ip <ip_1> --port <port_1> --ip <ip_2> --port <port_2>
```

Unlike the one that is spawned automatically, it won't update connections if a node fails and jobs are newly distributed.

### Writing tests

For using the test functionality you have to install pytest first: `pip3 install pytest`.  
This does **only** work for `PythonJob`s and `MARVELOJob`s, not "normal" `ExecutableJob`s!

**MARVELO** provides testing based on [pytest](https://docs.pytest.org/en/latest/contents.html).
If you haven't already, we recommend you take a look at pytest and how it works before you continue.

To start writing tests create a `tests` directory in you network's directory.
This is the directory where **MARVELO** looks for tests.
How exactly you structure your tests is up to you, but they must be detectable by pytest.

When testing we make use of the `fission.emulate` module.
It allows you to call you jobs like normal functions after wrapping them with an job emulator.
This is especially useful when writing `MARVELOJob`s because all pipes are created for you and you can easily feed the job with data.

> What is the difference between calling a PythonJob's `run` method and running it with an emulator?

Running it with an emulator gives a much better representation of what happens when executing it within **MARVELO**.
Besides just testing the `run` method, it also makes sure your job works as expected with the given pipes.

There a are basically 2 ways how you can access the jobs:

1. Import them like you would do in the config file and instantiate them like you would do in the config.
2. Use the `cfg_job` fixture provided by **MARVELO** to access the jobs defined in the config file.

There are some examples in `examples/demo_network_v4/tests`.

#### Defining specific jobs for testing

When instantiating new jobs and pipes you have to keep in mind that **MARVELO** caches all existing pipes and jobs.
This means when you where to instantiate a pipe with an id already in use this will result in an error.

They are cached in `fission.core.base` in dicts called `PIPES`, `JOBS`, `GROUPS` and `NODES`.
As job id are just increases for each new job you don't really have to worry about them, pipes are the issue here.  
To avoid this issue you either have to delete the according pipes from `PIPES` when you test is done or you call the `reset` function from `fission.core.base`.
This will clear **all** cached objects.
It actually sounds worse than it is, they are still accessible via the config file.

We recommend the following for testing with custom testing jobs:

```python
import pytest

from fission.core.base import reset
from fission.emulate import emulate

from my_network.jobs.jobs import MyJob
from my_network.pipes.pipes import MyPipe

# the job only needs to be created once as emulator spawns a subprocess
# and this exact job object is never changed.
@pytest.fixture(scope="module")
def my_job():
    _job = MyJob(
        inputs = [
            MyPipe(9001),
            ...
        ],
        outputs = [
            MyPipe(9101),
            ...
        ]
    )

    yield _job

    reset()

# create a new emulate object for each test.
# This should be done to avoid data being still left in the fifo pipes.
@pytest.fixture
def my_job_emulator(my_job):
    _emulator = emulate(my_job)

    yield _emulator

    _emulator.kill()

def test_my_test(my_job_emulator):
    ...

```

If you rename the `my_job` fixture to `fission_test_job` you can skip the emulator fixture and just use `fission_test_emulator` provided by **MARVELO**.
It will aromatically wrap the `fission_test_job` fixture with an emulator and will call `reset` before and after the fixture, just keep it in mind.
This will remove the need of calling reset in the fixture.

```python
import pytest

from fission.core.base import reset

from my_network.jobs.jobs import MyJob
from my_network.pipes.pipes import MyPipe

# the job only needs to be created once as emulator spawns a subprocess
# and this exact job object is never changed.
@pytest.fixture(scope="module")
def fission_test_job():
    _job = MyJob(
        inputs = [
            MyPipe(9001),
            ...
        ],
        outputs = [
            MyPipe(9101),
            ...
        ]
    )

    return _job

def test_my_test(fission_test_emulator):
    ...
```

Sometimes your job has different start parameters when initiating.
This can easily be added by adding parametrized fixtures to the `fission_test_job`.  
(Imports are skipped in the following)

```python
@pytest.fixture(params=[1, 5, 20])
def start_value(request):
    return request.param

@pytest.fixture(params=["last", "first"])
def mode(request):
    return request.param

@pytest.fixture
def fission_test_job(start_value, mode):
    _job = MyJob(
        start_value = start_value,
        mode = mode,
        inputs = [
            MyPipe(9001),
            ...
        ],
        outputs = [
            MyPipe(9101),
            ...
        ]
    )

    return _job

def test_my_test(fission_test_emulator):
    ...
```

Notice how we are now forced to remove the scope as dispy does not allow it when fixtures are parametrized.
To write useful test you most likely need access to the job parameters.
Luckily the emulator object stores the according job in it's `job` attribute.
Therefore you can access each parameter that is stored within the job object: `fission_test_emulator.job.<job_attribute>`.

#### Using jobs from the config file

You can also just use the jobs defined in your config file. This isn't exactly recommended because you tests will most likely stop working after changing the config file.

The fixture `fission_cfg` will give you the config module.
From there on you can access everything defined in the `config.py` module.

Additionally you can use `fission_cfg_jobs`.
This will give you a function which wrappes the jobs defined in the config.
Calling the function with an index, it will return an emulator for `config.JOBS[index]`.

```python
job = fission_cfg_jobs(0)
```

Will return an emulator object for the first job defined in the config.

#### Testing output files

By default the emulator executes jobs in the `.emulate` directory in your project.
This is shared between all networks, but as these are temp files this should not be a problem.

The emulator object has a `cwd` attribute which is the path where the job is executed.
By default this path is relative to the project root: `.emulate/<job_id>`.
There you can access all files you created within you job.

#### Marking slow tests

Job can be very time intensive, due to being computationally heavy or involving sleep statements to reduce the load for the network.
You can mark such tests with an decorator: `@pytest.mark.slow`.
These test will be skipped, unless you run the tests with the `--runslow` flag.

#### Running the tests

You can run the test as follows:

```bash
python3 manage.py my_network test
```

This is equivalent to `pytest my_network/tests`, except it includes the **MARVELO** plugins to add the functionality discussed before.
You can pass any additional arguments, like you would when running pytest normally.



