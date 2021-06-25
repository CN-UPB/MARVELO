import os
import logging
import types
import inspect
from importlib import import_module

from fission.core.base import JOBS, NODES, PIPES
from fission.core.groups import BaseGroup
from fission.core.network import Network
from fission.loader import CSVLoader, XMLLoader
from fission.core.jobs import LocalJob
from fission.core.nodes import LocalNode, MultiNode

logger = logging.getLogger(__name__)


def load_network(config, name=None, remote_root='', sanity_check=True, **kwargs):
    # load xml file if it is given
    if hasattr(config, "XML_FILE") and config.XML_FILE:
        if hasattr(config, "XML_ARGS"):
            xml_args = config.XML_ARGS
        else:
            xml_args = {}
        loader = XMLLoader(**kwargs)
        loader.load(config.XML_FILE)

    # load csv files if any
    loader = CSVLoader()

    csv_nodes = [n for n in NODES.values() if isinstance(n, str)]
    for path in csv_nodes:
        nodes = loader.load_nodes(path)
        print(f"Loaded {len(nodes)} nodes from {path}.")

    if config.CLIENT_IP:
        LocalNode(config.CLIENT_IP, name="LocalNode")
    else:
        LocalNode('localhost', name="LocalNode")

    # init groups
    for job in JOBS.values():
        # check DEFAULT_NODE
        if job.DEFAULT_NODE:
            NODES[job.DEFAULT_NODE].add_job(job)

        # check LocalJob
        if isinstance(job, LocalJob):
            if hasattr(config, "CLIENT_IP") and config.CLIENT_IP:
                NODES[config.CLIENT_IP].add_job(job)
            else:
                NODES['localhost'].add_job(job)

        # convert to GROUPS
        if isinstance(job.GROUPS, str):
            BaseGroup(job.GROUPS).add_job(job)
        elif isinstance(job.GROUPS, list):
            for g in job.GROUPS:
                BaseGroup(g).add_job(job)

        # convert dependencies
        if job.DEPENDENCIES == None:
            pass
        elif isinstance(job.DEPENDENCIES, str):
            try:
                assert os.path.isdir(job.DEPENDENCIES)
            except AssertionError:
                raise RuntimeError(
                    f"Dependencie {job.DEPENDENCIES} of {job} can`t be found or isn`t a directory.")
        elif isinstance(job.DEPENDENCIES, list):
            deps = job.DEPENDENCIES
            job.DEPENDENCIES = None
            for dep in deps:
                if isinstance(dep, str):
                    try:
                        assert os.path.isdir(dep)
                    except AssertionError:
                        raise RuntimeError(
                            f"Dependencie {dep} of {job} can`t be found or isn`t a directory.")
                    # check if dependencies already had been replaced
                    if isinstance(job.DEPENDENCIES, str):
                        raise RuntimeError(
                            f"You may only define one path in DEPENDENCIES of {job}. {dep} is the second one.")
                    else:
                        job.DEPENDENCIES = dep
                elif isinstance(dep, types.ModuleType) or inspect.isclass(dep):
                    if hasattr(job, '_modules'):
                        job._modules.append(dep)
                    else:
                        job._modules = [dep]
                else:
                    raise RuntimeError(
                        f"DEPENDENCIES of {job} may only contain modules or a path as a str")
        else:
            raise RuntimeError(
                f"DEPENDENCIES of job {job} must be str or list, not {type(job.DEPENDENCIES)}")

    for node in NODES.values():
        if isinstance(node.GROUPS, str):
            BaseGroup(node.GROUPS).add_node(node)
        elif isinstance(node.GROUPS, list):
            for g in node.GROUPS:
                BaseGroup(g).add_node(node)

    if hasattr(config, 'DEBUG_WINDOW'):
        debug = config.DEBUG_WINDOW
    else:
        debug = False

    if hasattr(config, 'HEAD_SIZE'):
        if isinstance(config.HEAD_SIZE, int) and config.HEAD_SIZE >= 1:
            for pipe in PIPES.values():
                pipe._head_size = config.HEAD_SIZE
        else:
            raise ValueError(f"HEAD_SIZE must be integer > 0, not {config.HEAD_SIZE}")

    if hasattr(config, "CLIENT_IP") and config.CLIENT_IP:
        client_ip = config.CLIENT_IP
    else:
        client_ip = "localhost"

    if hasattr(config, "PRE_COPY"):
        pre_copy = config.PRE_COPY
    else:
        pre_copy = False

    if sanity_check:
        for pipe in PIPES.values():
            if not pipe.complete():
                if not pipe.source:
                    raise RuntimeError("{pipe} defines no source.")
                if not pipe.destination:
                    raise RuntimeError("{pipe} defines no destination.")

    nodes = {ip: node for ip, node in NODES.items(
    ) if not isinstance(node, MultiNode)}

    network = Network(config.USER, JOBS, nodes, PIPES, debug=debug, name=name,
                      client_ip=client_ip, remote_root=remote_root, pre_copy=pre_copy)

    return network
