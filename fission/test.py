import pytest

from fission.core.base import reset
from fission.emulate import emulate


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


_config = None


@pytest.fixture
def fission_cfg_jobs():
    emulator = None

    def _cfg_jobs(index, path=".emulate"):
        nonlocal emulator
        emulator = emulate(_config.JOBS[index], path=path)
        return emulator
    yield _cfg_jobs

    emulator.kill()


@pytest.fixture
def fission_cfg():
    return _config


@pytest.fixture
def fission_test_emulator(fission_test_job, fission_reset):
    _emulator = emulate(fission_test_job)

    yield _emulator

    _emulator.kill()


@pytest.fixture
def fission_reset():
    reset()
    yield None
    reset()


def main(config, path, additional_args):
    global _config
    _config = config

    pytest.main(args=[path] + additional_args, plugins=["fission.test"])
