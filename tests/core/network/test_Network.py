import pytest
import fission.core.base as Base
from fission.core.base import JOBS, NODES, PIPES
from fission.core.base import BaseNode, BaseJob, BaseGroup, BasePipe
from fission.core.nodes import MultiNode
from fission.core.network import Network

#TODO rewrite for Linux


@pytest.fixture
def create_Nodes():
    #max n = 255
    def _create_Nodes(n):
        for i in range(n):
            yield BaseNode(f"198.168.4.{i+1}")
    yield _create_Nodes
    Base.reset()

@pytest.fixture
def create_Jobs():
    def _create_Jobs(n):
        for i in range(n):
            yield BaseJob()
    yield _create_Jobs
    Base.reset()

def test_add_node(create_Nodes):
    #create network
    #network1 = create_Network
    network1 = Network("asn")
    assert network1.user == "asn"
    assert network1.jobs == {}
    Node1,  = list(create_Nodes(1))
    #test with Node object
    network1.add_node(Node1)
    assert Node1 in network1.nodes.values()
    #test with non Node object
    with pytest.raises(RuntimeError) as excinfo:
        network1.add_node("ThisIsNotANode")
    assert f"Tried adding {str} as node to network." in str(excinfo)
    
def test_add_job(create_Jobs):
    #create network
    #network1 = create_Network
    network2 = Network("pi")
    assert network2.user == "pi"
    assert network2.jobs == {}
    Job1, = list(create_Jobs(1))
    #test with job object
    network2.add_job(Job1)
    assert Job1 in network2.jobs.values()
    #test with a non-job
    with pytest.raises(RuntimeError) as excinfo:
        network2.add_job("ThisIsNotAJob")
    assert f"Tried adding {str} as job to network." in str(excinfo)
    

def test_is_ready(create_Jobs, create_Nodes):
    #create Network
    #network1 = create_Network
    network3 = Network("ttt")
    assert network3.user == "ttt"
    assert network3.jobs == {}
    Job1, Job2, = list(create_Jobs(2))
    Node1, =list(create_Nodes(1))
    network3.add_job(Job1)
    network3.add_job(Job2)
    network3.add_node(Node1)
    #check function
    Job1.allocate(Node1)
    assert network3.is_ready() == False
    Job2.allocate(Node1)
    assert network3.is_ready() == True

def test_up(create_Nodes):
    #create network
    # network1 = create_Network
    network4 = Network("opel")
    assert network4.user == "opel"
    assert network4.jobs == {}
    Node1, = list(create_Nodes(1))
    Node1.ip = "198.168.4.1" #for windows
    network4.add_node(Node1)
    #test function
    network4.up("198.168.4.1") 
    assert Node1.active == True
    with pytest.raises(RuntimeError) as excinfo:
        network4.up("NodeNotExisting")
    assert f"Node with NodeNotExisting does not exist in Network database." in str(excinfo)

def test_down(create_Jobs, create_Nodes):
    #create network
    #network1 = create_Network
    network5 = Network("ford")
    assert network5.user == "ford"
    assert network5.jobs == {}
    Job1, Job2, = list(create_Jobs(2))
    Node1, =list(create_Nodes(1))
    Node1.ip = "198.168.4.1" #for windows
    Node1.max_jobs = 4       #for windows
    network5.add_job(Job1)
    network5.add_job(Job2)
    network5.add_node(Node1)
    Node1.add_job(Job2)
    #test function
    closed_jobs = network5.down("198.168.4.1")
    assert closed_jobs == [Job2]
    assert Node1.active == False
    with pytest.raises(RuntimeError) as excinfo:
        network5.down("NodeNotExisting")
    assert f"Node with NodeNotExisting does not exist in Network database." in str(excinfo)

#TODO terminated(), restart(), finished(), running()
#DISPY ID? also for restart(), finished(), running()
# def test_terminated(create_Network, create_Jobs):
#     #create network
#     network1 = create_Network
#     Job1, = list(create_Jobs(2))
#     network1.add_job(Job1)
#     network.terminated()

def test_get_node_fewest_job(create_Jobs, create_Nodes):
    #create network
    #network1 = create_Network
    network6 = Network("fiat")
    assert network6.user == "fiat"
    assert network6.jobs == {}
    Job1, Job2, = list(create_Jobs(2))
    Node1, Node2, = list(create_Nodes(2))
    #test_function
    network6.add_job(Job1)
    network6.add_job(Job2)
    network6.add_node(Node1)
    network6.add_node(Node2)
    Node1.active = True #normally network.up(ip) for linux
    Node2.active = True #normally network.up(ip) for linux
    Node1.max_jobs = 4
    Node2.max_jobs = 4
    
    for job in JOBS.values():
        #convert to GROUPS
        if isinstance(job.GROUPS, str):
            BaseGroup(job.GROUPS).add_job(job)
        elif isinstance(job.GROUPS, list):
            for g in job.GROUPS:
                BaseGroup(g).add_job(job)
    for node in NODES.values():
        if isinstance(node.GROUPS, str):
            BaseGroup(node.GROUPS).add_node(node)
        elif isinstance(node.GROUPS, list):
            for g in node.GROUPS:
                BaseGroup(g).add_node(node)

    Node1.add_job(Job1)
    node = network6._get_node_fewest_jobs(Job2)
    assert node == Node2


def test_init_Network():
    network1 = Network(user="pi")
    assert network1.user == "pi"
    assert network1.jobs == {}
    assert network1.nodes == {}
    node = BaseNode("192.168.4.2")
    job = BaseJob()

    network2 = Network(user="asn")
    assert network2.user == "asn"
    assert network2.jobs == {}
    assert network2.nodes == {}
    network2.add_job(job)
    assert network2.jobs == {1: job}
    network2.add_node(node)
    assert network2.nodes == {None : node} #fails for windows bc of dispy

    network3 = Network(user="super")
    assert network3.user == "super"
    assert network3.jobs == {}
    assert network3.nodes == {}


def test_allocate_jobs(create_Jobs, create_Nodes):
    #creating Network
    network1 = Network("pi")
    Node1, Node2, Node3, = list(create_Nodes(3))
    Job1 = BaseJob(outputs=[BasePipe(1)])
    Job2 = BaseJob(inputs=[BasePipe(1)],outputs=[BasePipe(2)])
    Job3 = BaseJob(inputs=[BasePipe(2)])
        
    #---
    Node1.ip = "192.168.4.1"
    Node2.ip = "192.168.4.2"
    Node3.ip = "192.168.4.3"
    #---
    network1.add_job(Job1)
    network1.add_job(Job2)
    network1.add_job(Job3)
    network1.add_node(Node1)
    network1.add_node(Node2)
    network1.add_node(Node3)

    for job in JOBS.values():
        #convert to GROUPS
        if isinstance(job.GROUPS, str):
            BaseGroup(job.GROUPS).add_job(job)
        elif isinstance(job.GROUPS, list):
            for g in job.GROUPS:
                BaseGroup(g).add_job(job)

    for node in NODES.values():
        if isinstance(node.GROUPS, str):
            BaseGroup(node.GROUPS).add_node(node)
        elif isinstance(node.GROUPS, list):
            for g in node.GROUPS:
                BaseGroup(g).add_node(node)
    
    #Iinitalze Nodes
    #Node 1 and 2 will be alive, Node 3 will die
    #---
    Node1.max_jobs = 4
    Node2.max_jobs = 4
    Node3.max_jobs = 4
    #---
    Node1.add_jobs([Job1])
    Node2.add_jobs([Job2])
    Node3.add_jobs([Job3])
    network1.up("192.168.4.1")
    network1.up("192.168.4.2")
    network1.up("192.168.4.3")
    Node1.mac = "m1:b1:c1:z1"
    Node2.mac = "m2:b2:c2:z2"
    Node3.mac = "m3:b3:c3:z3"
    Node1.routing_table = {"mac": "m2:b2:c2:z2" , "TQ": 198}
    Node2.routing_table = {"mac": "m1:b1:c1:z1" , "TQ": 198}
    Node1._avg_info = {"cpu": 20, "memory": None, "disk": None, "swap": 50} 
    Node2._avg_info = {"cpu": 50, "memory": None, "disk": None, "swap": 50}
    
    network1.down("192.168.4.3")

    node = network1.allocate_jobs(ssh= False)
    assert node == [Node2]
    assert len(Node2.jobs) == 2
    assert len(Node3.jobs) == 0    