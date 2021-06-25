import logging

from dispy import NodeAllocate
from fission.core.base import BaseNode

logger = logging.getLogger(__name__)


class MultiNode(NodeAllocate):

    GROUPS = "ALL"

    def __init__(self, host, port=None, cpus=0, depends=[], setup_args=()):
        super().__init__(host, port=port, cpus=cpus, depends=depends, setup_args=setup_args)

        self.GROUPS = self.GROUPS
        self.max_jobs = 0


class LocalNode(BaseNode):

    GROUPS = "LOCAL"

    def __init__(self, host, name):
        self.ip = host
        self._name = name
        self.active = True
        self.max_jobs = 1000


class NodeInfo():
    def __init__(self, node, cpu, memory, disk, swap, TQ):
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.swap = swap
        self.TQ = TQ
        self._node = node
