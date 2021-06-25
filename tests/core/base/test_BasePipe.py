import unittest
import os
import pytest

import fission.core.base as base
from fission.core.jobs import BaseJob, ExecutableJob
from fission.core.pipes import BasePipe

@pytest.fixture
def create_Pipes():
    Pipe1 = BasePipe(1)
    Pipe2 = BasePipe(2)
    Pipe3 = BasePipe(3)
    yield Pipe1, Pipe2, Pipe3
    base.reset()

def test_set_source(create_Pipes):
    
    Pipe1, Pipe2, Pipe3 = create_Pipes
    Job = BaseJob(outputs=[Pipe1])
    assert Pipe1.source == Job

    with pytest.raises(RuntimeError) as excinfo:
        Job1 = BaseJob(outputs=[Pipe1, Pipe1])
    assert f"Source of pipe {Pipe1.id} was defined multiple times." in str(excinfo)

    with pytest.raises(RuntimeError) as excinfo:
        Job2 = BaseJob(inputs=[Pipe2], outputs=[Pipe2])
    assert f"PIPE {Pipe2.id}: You can't loop back pipes to same job" in str(excinfo)

    Pipe3.SOURCE_JOBS = [ExecutableJob]
    with pytest.raises(RuntimeError) as excinfo:
        Job3 = BaseJob(outputs=[Pipe3])
    print(str(excinfo))
    assert f"Given source job is not listed in SOURCE_JOB" in str(excinfo)

def test_set_destination(create_Pipes):
        Pipe1, Pipe2, Pipe3 = create_Pipes
        Job = BaseJob(inputs=[Pipe1])
        assert Pipe1.destination == Job

        with pytest.raises(RuntimeError) as excinfo:
            Job1 = BaseJob(inputs=[Pipe1, Pipe1])
        assert f"Destination of pipe {Pipe1.id} was defined multiple times." in str(excinfo)

        Pipe2.DESTINATION_JOBS = [ExecutableJob]
        with pytest.raises(RuntimeError) as excinfo:
            Job2 = BaseJob(inputs=[Pipe2])
        assert f"Given destination job is not listed in DESTINATION_JOBS" in str(excinfo)

        with pytest.raises(RuntimeError) as excinfo:
            Job3 = BaseJob(outputs=[Pipe3], inputs=[Pipe3])
            assert f"PIPE {Pipe1.id}: You can't loop back pipes to same job ({Job3})." in str(excinfo)

# def test_different_pipes_same_id():
#     with pytest.raises(RuntimeError) as excinfo:
#         BasePipe(10)
#         ArrayPipe(10)
#     assert f"Pipe with id 10 was called on {ArrayPipe} and is {BasePipe}" in str(excinfo)
#     base.reset()