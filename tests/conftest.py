import pytest

import fission.core.base as base

@pytest.fixture
def config():
    class _config():
        pass
    dummy_config = _config()
    return dummy_config

@pytest.fixture
def fission_node():
    """Returns a function with returns a BaseNode with given ip
    """
    def _node(ip):
        return base.BaseNode(ip)
    yield _node
    base.reset()


@pytest.fixture
def fission_nodes():
    """Returns a function with returns a list with given number of BaseNodes (max 253).
    """
    def _nodes(num):
        assert num <= 253
        return [base.BaseNode(f"192.168.4.{i}") for i in range(1, num + 1)]
    yield _nodes
    base.reset()


@pytest.fixture
def fission_job():
    """Returns a BaseJob
    """
    yield base.BaseJob()
    base.reset()


@pytest.fixture
def fission_jobs():
    """Returns a function which returns given number of BaseJobs.
    """
    def _jobs(num):
        return [base.BaseJob() for i in range(num)]
    yield _jobs
    base.reset()


@pytest.fixture
def fission_pipe():
    """Returns BasePipe with id 1.
    """
    yield base.BasePipe(1)
    base.reset()


@pytest.fixture
def fission_pipes():
    """Returns a function which returns given number of BasePipes.
    """
    def _pipes(num):
        return [base.BasePipe(i) for i in range(1, num + 1)]
    yield _pipes
    base.reset()
