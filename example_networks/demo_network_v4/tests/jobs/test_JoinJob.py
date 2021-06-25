import pytest

from fission.core.base import reset
from fission.core.pipes import PicklePipe
from fission.emulate import emulate

from demo_network_v4.jobs.jobs import JoinJob


@pytest.fixture(params=[8000, 9000])
def pipe_id_offset(request):
    return request.param


#@pytest.mark.usefixture("fission_reset")
@pytest.fixture()
def fission_test_job(pipe_id_offset):
    # initiates a new job
    _job = JoinJob(
        inputs=[
            PicklePipe(pipe_id_offset + 1),  # this is the operator
            PicklePipe(pipe_id_offset + 2),
            PicklePipe(pipe_id_offset + 3),
            PicklePipe(pipe_id_offset + 4),
        ],
        outputs=[
            PicklePipe(pipe_id_offset + 101),
            PicklePipe(pipe_id_offset + 102),
            PicklePipe(pipe_id_offset + 103),  # This is the operator output
        ]
    )

    yield _job

    # This will remove the buffered job, pipes, groups and nodes which resulted from loading the config.
    # They are still accessible from the config or via the cfg_job fixture.
    # reset()


def test_add_operator(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(4)

    args = [1, 2, 3]

    _sum = sum(args)

    # this is a async job.
    # Therefore we need to clear the default value by passing some data
    # Default is +, therefore we assume first call is also add
    assert job("+", *args) == [_sum, _sum, '+']

    assert job("+", *list(reversed(args))) == [_sum, _sum, '+']


def test_mult_operator_config_job(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(4)

    args = [1, 2, 3]

    # operator is async, override operator
    job("*", *args)

    # actually test
    assert job("*", *args) == [6, 6, '*']


def test_mult_operator_custom_job(fission_test_emulator):
    # access the 5. job from the config file
    job = fission_test_emulator

    args = [1, 2, 3]

    # behaves as expected, as there is no async pipe in place
    assert job("*", *args) == [6, 6, '*']


def test_div_operator_config_job(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(4)

    args = [8, 2, 4]

    # operator is async, override operator
    job("/", *args)

    # actually test
    assert job("/", *args) == [1, 1, '/']


def test_div_operator_custom_job(fission_test_emulator):
    # access the 5. job from the config file
    job = fission_test_emulator

    args = [8, 2, 4]

    # behaves as expected, as there is no async pipe in place
    assert job("/", *args) == [1, 1, '/']
