import pytest
from fission.core.jobs import PythonJob
from fission.core.base import BaseNode, BaseJob, BaseGroup, BasePipe
from fission.core.base import JOBS, NODES, PIPES
from fission.core.network import Network
import fission.core.base as Base

class SquaredJob(PythonJob):
    def run(self, a):
        print(a**2)
    
    def preference(self, nodeinfo, *args, **kwargs):
        for node in nodeinfo:
            if node.cpu > 90:
                return node
        return None



def test_preference():
    #creating Network
    network1 = Network("pi")
    Node1 = BaseNode("192.168.4.1")
    Node2 = BaseNode("192.168.4.2")
    Node3 = BaseNode("192.168.4.3")
    Job1 = BaseJob(outputs=[BasePipe(1)])
    Job2 = BaseJob(inputs=[BasePipe(1)],outputs=[BasePipe(2)])
    Job3 = SquaredJob(inputs=[BasePipe(2)])
        
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
    Node1._avg_info = {"cpu": 89, "memory": None, "disk": None, "swap": 0} 
    Node2._avg_info = {"cpu": 91, "memory": None, "disk": None, "swap": 70}
    
    network1.down("192.168.4.3")

    node = network1.allocate_jobs(ssh= False)
    assert node == [Node2]
    assert len(Node2.jobs) == 2
    assert len(Node3.jobs) == 0 


