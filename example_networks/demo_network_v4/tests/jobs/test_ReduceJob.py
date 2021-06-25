import pytest

from fission.core.base import PIPES, reset
from fission.core.pipes import PicklePipe
from fission.emulate import emulate

from demo_network_v4.jobs.jobs import ReduceJob
from demo_network_v4.pipes.pipes import ReducePipe


def test_reduce_job_from_config(fission_cfg_jobs):
    job = fission_cfg_jobs(5)

    arg = (1, 2, 3, 4, 5)
    job(arg)

    assert job(arg) == [sum(arg)]

# set the scope to avoid problems with buffered objects
@pytest.fixture(scope="module")
def fission_test_job():

    _job = ReduceJob(
        inputs=[
            ReducePipe(9001)
        ],
        outputs=[
            PicklePipe(9002)
        ]
    )

    yield _job

    # This will also remove the buffered job, pipes, groups and nodes which resulted from loading the config.
    # They are still accessible from the config or via the cfg_job fixture.
    reset()


def test_reduce_job_custom(fission_test_emulator):
    job = fission_test_emulator

    arg = (1, 2, 3, 4, 5)
    job(arg)

    assert job(arg) == [sum(arg)]


def test_reduce_job_custom2(fission_test_emulator):
    job = fission_test_emulator

    arg = (6, 7, 8, 9, 10)
    job(arg)

    assert job(arg) == [sum(arg)]
