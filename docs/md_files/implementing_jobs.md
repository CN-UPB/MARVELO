# Implementing Jobs

This page covers what you need to think about when making a job for **MARVELO**.  

## Overview

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

## Predefined Jobs
There are some already implemented jobs that may be useful. 

### CSVSinkJob
Writes all 

### InteractiveJob
Opens an interactive console at the client, where one can type and send it to jobs during runtime.

### LoggingJob and LoggingSinkJobs
When a job inherits from  **LoggingJob** it logs times, CPU utilization, etc. It has to send it to a **LoggingSinkJob**, which writes it down in a CSV file.

### ClockJob
Can be used as a source job to synchonize multiple source jobs.

### ForwardingJob
This Job forwards all incoming data to its output pipe.



## GROUPS, DEFAULT_NODE and MAX_QUEUE

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

## Python Jobs

Python jobs are the easiest way to implement a job for **MARVELO** and are recommended unless you have to use another language due to compatibility or performance issues/concerns.

To start developing a Python job you need to import `PythonJob` from `fission.core.jobs`. 
This is the class implementing all the boilerplate code for interacting with pipes, converting Python objects to a byte representation and few other things.  
There are two methods you are meant to override:

- `setup`
- `run`

### Setup your job

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

### Implementing the actual logic

The `run` method defines the actual job being executed. 

#### Source Job

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

### Connector and Sink Jobs

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

### Local job

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

### Using modules

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

### MARVELO Head interface

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


## Executable Jobs

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

### MARVELO Head

If you set the `HEAD` attribute, you have to read `HEAD_SIZE` bytes before reading the actual data.  
You will also have to write the head of the same size to the output before writing any data.  
`HEAD_SIZE` defaults to 1.

The first 3 bytes are reserved by **MARVELO**, for more information see [Synchronization](fission/Synchronization.md).


