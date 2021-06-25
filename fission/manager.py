import inspect
import logging
import multiprocessing
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
import time
from glob import glob
from importlib import import_module
from pathlib import Path

import dispy

import fission.core.base
import fission.core.jobs
import fission.core.nodes
import fission.core.pipes
import fission.remote.debug as debug
import fission.remote.synchronization as sync
from fission.build import load_network
from fission.core.base import GROUPS, JOBS, NODES, PIPES, MetaJob, MetaPipe
from fission.core.nodes import LocalNode, MultiNode
from fission.remote.debug import MultiWrite
from fission.remote.wrapper import pipe_wrapper_sync
from fission.templates import config, manage

logger = logging.getLogger(__name__)


def configurate_logger(file, level, shell_format='%(levelname)s ->  %(message)s',
                       file_format='%(asctime)s - %(name)s - %(levelname)s [%(process)s]- %(message)s'):
    logging.getLogger().setLevel(logging.getLevelName(level))
    logger = logging.getLogger("fission")

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(f'{file}')
    c_handler.setLevel(logging.getLevelName(level))
    f_handler.setLevel(logging.getLevelName(level))

    # Create formatters and add it to handlers
    c_format = logging.Formatter(shell_format)
    f_format = logging.Formatter(file_format)
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def execute_from_command_line(argv):
    network = argv[1].strip()
    command = argv[2].strip()
    
    if not command == "startnetwork":
        try:
            config = import_module(os.environ['FISSION_CONFIG_MODULE'])
            configurate_logger(config.LOG_FILE, config.LOG_LEVEL)
        except KeyError:
            pass

    # TODO sanity check arguments
    if len(argv) > 2:
        args = [arg.strip() for arg in argv[3:]]
    else:
        args = []

    if Path(argv[0]).name == "fission_admin.py":
        if command == "startproject":
            start_project(network)
        else:
            raise RuntimeError(
                f"You may only use 'startproject' with fission_admin.py")
    else:
        if command == "shell":
            execute_cmd(config, network)
        elif command == "run":
            execute_network(config, network)
        elif command == "simulate":
            execute_simulation(config, network, *args)
        elif command == "test":
            run_tests(config, network, args)
        elif command == "startnetwork":
            start_network(network)
        elif command == "graphviz":
            make_pdf(config, network)
        elif command == "show":
            matplotlib_graph(config)
        elif command == "interactive":
            start_interactive(config)
        elif command == "collect":
            start_collection(config, network)
        else:
            raise RuntimeError(f"Unknown command {command}")


def execute_cmd(config, network):
    from fission.cmd import FissionCMD
    network = load_network(config, name=network)
    fission = FissionCMD(config.USER, network)
    fission.cmdloop()


def get_dependencies(pre_copy):
    # get all classes that need to be pickled
    dependencies = [MetaJob, MetaPipe]
    dependencies.extend([debug, sync,
                         fission.core.base,
                         fission.core.pipes,
                         fission.core.jobs,
                         fission.core.nodes])
    if pre_copy:
        for job in JOBS.values():
            if not isinstance(job, fission.core.jobs.LocalJob):
                dependencies.extend(job.get_dependencies())

    return dependencies


def execute_network(config, network):
    try:
        root = config.REMOTE_ROOT
        network = load_network(config, remote_root=root, name=network)

        dependencies = get_dependencies(network.pre_copy)

        network.delete_files()

        # some sanity checks
        if len(NODES) == 0:
            raise RuntimeError("No nodes defined.")

        if len(network.jobs) == 0:
            raise RuntimeError("No jobs defined.")

        if hasattr(config, 'PULSE_INTERVAL'):
            pulse_interval = config.PULSE_INTERVAL
        else:
            pulse_interval = 0.1

        print("Creating Cluster...")
        nodes = [n for n in network.nodes.values()
                 if not isinstance(n, LocalNode)]

        cluster = dispy.JobCluster(pipe_wrapper_sync, nodes=nodes, depends=dependencies, cluster_status=network.status_callback,
                                   pulse_interval=pulse_interval, ping_interval=1, ip_addr=config.CLIENT_IP, loglevel=dispy.logger.INFO)
        time.sleep(2)  # TODO make discovery delay settable
        cluster.print_status()

        network.cluster = cluster
        # allocated jobs to active nodes
        network.allocate_jobs()
        # submit all jobs to dispy cluster
        network.submit(cluster)
        # wait for cluster operations to finish
        try:
            if network.debug:
                tmp_dir = tempfile.mkdtemp(prefix='fission')
                fifo = f"{tmp_dir}/debug.fifo"
                os.mkfifo(fifo)

                debug_window = open_debug_window(fifo)
                logger.info(f"Created pipe for debug window: {fifo}")
                network.debug_pipe = open(fifo, "w")
                network.update_debug_window()
        except Exception as e:
            network.shutdown()
            raise e

        try:
            network.wait()
        except KeyboardInterrupt:
            network.shutdown()
    except KeyboardInterrupt:
        network.shutdown()


def cwd_wrapper(func, cwd, *args, **kwargs):
    os.chdir(cwd)
    func(*args, **kwargs)


def execute_simulation(config, network_name, root=""):
    network = load_network(config)

    if not root:
        root = f"{os.getcwd()}/{network_name}/simulation/"

    os.makedirs(root + "/fifo", exist_ok=True)

    with open(f"{root}/info.txt", "w") as f:
        max_length = max([len(str(id)) for id in network.jobs.keys()])
        for id, j in network.jobs.items():
            f.write('{:{align}{width}} - {job}\n'.format(id,
                                                         align='>', width=max_length, job=j))

    for pipe in PIPES.values():
        path = f"{root}/fifo/{pipe.id}.fifo"

        if os.path.exists(path):
            os.remove(path)
            os.mkfifo(path)
        else:
            os.mkfifo(path)

    for job in JOBS.values():
        dest = f"{root}/{job.id}/"
        if os.path.exists(dest):
            shutil.rmtree(dest)
        if job.DEPENDENCIES:
            shutil.copytree(job.DEPENDENCIES, dest)
        os.makedirs(dest, exist_ok=True)

    processes = []

    for pipe in PIPES.values():
        pipe._destination = "localhost"
        pipe._source = "localhost"

    for job in JOBS.values():
        args = (pipe_wrapper_sync, f"{root}/{job.id}", job, root)
        kwargs = {'debug': False}

        if job.CREATES_SUBPROCESS:
            kwargs["debug"] = True

        new_process = multiprocessing.Process(
            target=cwd_wrapper, args=args, kwargs=kwargs,  name=f"{job}", daemon=True)
        processes.append(new_process)

    for p in processes:
        p.start()

    logger.debug("Entering join.")
    try:
        for p in processes:
            logger.info(f"Joining {p}")
            p.join()
    except KeyboardInterrupt:
        pass


def start_project(name):
    os.mkdir(name)
    print("Copying 'manage.py'...")
    with open(f"{name}/manage.py", "w") as f:
        f.write(inspect.getsource(manage))
    start_network(f"{name}/shared", create_config=False)


def start_network(name, create_config=True):
    print(f"Starting {name} network...")
    modules = ['jobs', 'nodes', 'pipes']
    dirs = ['source']

    for d in modules + dirs:
        os.makedirs(f"{name}/{d}")

    Path(f"{name}/__init__.py").touch()

    for m in modules:
        print(f"Creating {m} module...")
        Path(f"{name}/{m}/__init__.py").touch()
        Path(f"{name}/{m}/{m}.py").touch()

    if create_config:
        print("Copying 'config.py'...")
        with open(f"{name}/config.py", 'w') as f:
            f.write(inspect.getsource(config))


def make_pdf(config, network):
    import traceback
    try:
        from fission.visualize import generate_job_graph
        path = f"{network}/network"
        network = load_network(config)

        generate_job_graph(network, path)
    except ImportError:
        print(traceback.format_exc)
        print("Error while importing.")
        print("Did you install the graphviz module?")
        print("'pip3 install graphviz'")
    except Exception:
        print(traceback.format_exc())
        print("Maybe you need to install graphviz and graphviz devtools:")
        print("'sudo apt install graphviz'")
        print("'sudo apt install libgraphviz-dev'")


def matplotlib_graph(config):
    import traceback
    try:
        from fission.visualize import show_job_graph
        network = load_network(config)

        show_job_graph(network)
    except ImportError:
        print(traceback.format_exc())
        print("Error while importing.")
        print("Did you install matplotlib and networkx?")


def start_interactive(config):
    from code import interact
    from fission.emulate import emulate

    directory = ".emulate"

    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(directory, exist_ok=True)
    # os.chdir(directory)

    # Disable sanity checks so network does not have to be complete
    network = load_network(config, sanity_check=False)

    env = {
        'network': network,
        'JOBS': JOBS,
        'PIPES': PIPES,
        'NODES': NODES,
        'GROUPS': GROUPS,
        'emulate': emulate,
    }
    print(
        f"Staring Python Interactive console.\nFollowing variables are defines: {list(env.keys())}")
    interact(local=env)


def open_debug_window(pipe):
    debug_window = subprocess.Popen([
        f'lxterminal --command="fission_debug.py -p {pipe}"'],
        shell=True, preexec_fn=os.setsid,
        stderr=subprocess.DEVNULL)

    return debug_window


def start_collection(config, network):

    root = config.REMOTE_ROOT
    current_dir = os.getcwd()
    current_dir_network = current_dir + "/" + network
    mkdir_command = "mkdir -p {path}/{dirname}"

    network = load_network(config, remote_root=root, name=network)
    # TODO:watch if sanity_check
    nodes = network.nodes.values()

    print(f"make dir at {current_dir}")
    error = os.system(mkdir_command.format(
        path=current_dir_network, dirname='collection'))
    if error:
        raise ValueError

    for node in nodes:
        if node.ip == config.CLIENT_IP:
            print(f"Collecting data from node {node.ip}")
            cp_command = "cp -r  {dest}/{logfilename} {src}/{dirname}/{logname}"
            loggingname = f"fission-{node.ip.replace('.','-')}.log"
            error = 0
            error = os.system(cp_command.format(
                src=current_dir_network, dirname='collection', user=network.user, ip=node.ip, dest=current_dir, logname=loggingname, logfilename=config.LOG_FILE))
        else:
            print(f"Collecting data from node {node.ip}")
            loggingname = f"fission-{node.ip.replace('.','-')}.log"
            scp_command = "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=error -r  {user}@{ip}:{dest}/fission.log {src}/{dirname}/{logname}"
            error = 0
            error = os.system(scp_command.format(
                src=current_dir_network, dirname='collection', user=network.user, ip=node.ip, dest=root, logname=loggingname))

            if error:
                logger.warn(f"Collecting from {node.ip} failed with code {error}")
            else:
                logger.debug(f"Collecting from {node.ip} succeeded")

def run_tests(config, network, additional_args):
    from fission.test import main
    path = Path(network)/Path("tests")
    main(config, str(path), additional_args)
