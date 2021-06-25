import pytest

from fission.core.pipes import PicklePipe

from shared.jobs.jobs import SourceJob


@pytest.mark.slow
def test_default_source(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(1)

    for i in range(1, 11):
        assert job() == [i, i]


@pytest.mark.slow
def test_step_source(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(3)

    for i in range(1, -9, -1):
        assert job() == [i, i]


@pytest.mark.slow
def test_start_source(fission_cfg_jobs):
    # access the 5. job from the config file
    job = fission_cfg_jobs(2)

    for i in range(20, 41, 2):
        assert job() == [i, i]


@pytest.fixture(params=[-20, 0, 20, 100])
def start(request):
    return request.param


@pytest.fixture(params=[-5, 1, 20])
def step(request):
    return request.param


@pytest.fixture
def fission_test_job(start, step):
    _job = SourceJob(
        start=start,
        step=step,
        delay=0,
        outputs=[
            PicklePipe(9001),
        ]
    )
    return _job

def test_with_parameterizing(fission_test_emulator):
    job = fission_test_emulator

    _job = job.job

    start = _job.value
    end = _job.value + _job.step * 100 + 1
    step = _job.step

    for i in range(start, end, step):
        assert [i] == job() 