# Debugging

## Simulate

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

## Interactive

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

### Pipe emulation

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

### Job emulation

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

## Debugging console

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

## Writing tests

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

### Defining specific jobs for testing

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

### Using jobs from the config file

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

### Testing output files

By default the emulator executes jobs in the `.emulate` directory in your project.
This is shared between all networks, but as these are temp files this should not be a problem.

The emulator object has a `cwd` attribute which is the path where the job is executed.
By default this path is relative to the project root: `.emulate/<job_id>`.
There you can access all files you created within you job.

### Marking slow tests

Job can be very time intensive, due to being computationally heavy or involving sleep statements to reduce the load for the network.
You can mark such tests with an decorator: `@pytest.mark.slow`.
These test will be skipped, unless you run the tests with the `--runslow` flag.

### Running the tests

You can run the test as follows:

```bash
python3 manage.py my_network test
```

This is equivalent to `pytest my_network/tests`, except it includes the **MARVELO** plugins to add the functionality discussed before.
You can pass any additional arguments, like you would when running pytest normally.



