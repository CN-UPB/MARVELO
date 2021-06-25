# Implementing Pipes

This section covers what you need to think about when making a pipe for **MARVELO**.

## Overview

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


## Predefined Pipes

The following pipes are predefined:

- `PicklePipe`
- `JSONPipe`
- `BytesPipe`

### PicklePipe

The PicklePipe, as the name suggests, implements a pipe using [pickle](https://docs.python.org/3/library/pickle.html) and is therefore very suitable for communicating between Python jobs without worrying about too much.
Only thing you have to worry about is to make sure you defined the dependencies correctly at both ends when sending objects from custom modules. Described [here](Create-a-Job#using-modules).

As this is Python specific, it is not suitable for communicating with any Executable job running some other language

### JSONPipe

This pipe sends data in the JSON format it therefore is very versatile. 
It relies on sending JSON in one line with an ending line break to distinguish between multiple in-/outputs.

This does not have to bother you when using Python job. 
You just need to stick to types that are convertible according to [this table](https://docs.python.org/3/library/json.html?highlight=jsondecoder#json.JSONDecoder).
Otherwise errors will occur while converting Python objects.


### BytesPipe

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

## Implementing my own pipe

We highly recommend to take a look at the `fission.core.pipes` module see a few examples of pipe implementations.

There are 5 methods that are essential to a pipes behaviour:

### Python job specific

#### `read(file_obj)`

This method take a file_obj opened in binary read mode and reads a block from it.  
It is supposed to return bytes but may also return something else if it is inefficient to read the bytes before converting it to Python objects.
E.g. the `PicklePipe` violates this rule.

#### `unpack(data)`

This method it called with what ever [read](#readfileobj) returns.  
It is supposed to return a Python object created from the bytes read in [read](#readfileobj).
The default implementation always returns `data`.  
It is meant to convert the received bytes from the network to a Python object suitable for the `run` method of the job.

#### `write(file_obj, data)`

This method is passed a file opened in binary write mode and data it is supposed to write to the file object.  
`data` is what ever [pack](#packdata) returns and should be bytes.

#### `pack(data)`

This method is meant to convert return values of the `run` method of a job into bytes to be able to send it across the network.

### General

#### `read_wrapper(file_obj)`

This method will be similar to the [read](#readfileobj) method.
It is called in the wrapper when reading from a jobs output pipe and therefore not only effecting Python jobs but Executable jobs.
Other than [read](#readfileobj) this method **has to return bytes**.  
By default this method just calls [read](#readfileobj) and returns it return value.

> Why do we have this method?

Taking the `PicklePipe` as an example, we can't use `pickle.load` to read from a pipe because necessary modules might not be loaded in the wrapper.  
Therefore we need a method that only reads a bytes representation.
Doing so each time before converting it to Python objects would be inefficient, therefore we have two different methods.

## ASYNC and Optional Pipes

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

## Pipes as bridges between Executable jobs and Python jobs

As stated in [Python job specific](#python-job-specific), there are methods only called by Python jobs.  
Still putting the effort into developing all 5 methods listed [here](#implementing-my-own-pipe) is worth it.  
On one hand you can use the pipes to easily connect Python and Executable jobs, on the other handy it is very useful for debugging and testing a Executable like described in [debugging](Debugging).


