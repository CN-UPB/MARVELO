import unittest
import os
import shutil

from dispy import logger as dispy_logger
import fission.core.base as base
from fission.core.base import BaseNode
from fission.core.base import BaseJob

dispy_logger.setLevel(dispy_logger.ERROR)

# TODO rewrite for pytest

class TestNode(unittest.TestCase):

    def setUp(self):
        self.correct_IP_Node = BaseNode("192.168.4.2")
        self.wrong_IP_Node = BaseNode("Some.Wrong.IP.LUL")

        os.mkdir(".temp")
        os.chdir(".temp")
        
        self.test_info_average = []
        self.test_info_numbers = []

        self.Job1 = BaseJob()
        self.Job2 = BaseJob()
        self.Job3 = BaseJob()
        self.Job4 = BaseJob()
        self.Job5 = BaseJob()
        self.Job_list_4 = [self.Job1,self.Job2,self.Job3,self.Job4]
        self.Job_list_5 = [self.Job1,self.Job2,self.Job3,self.Job4,self.Job5]


    def tearDown(self):
        os.chdir("..")
        shutil.rmtree(".temp")
        base.NODES =  {}
        base.JOBS = {}

    
    def test_info_calculation(self):
        #approved values
        self.test_info_numbers = [[2*i,i/2,i,i] for i in range(70)]
        for i in range(70):
            if i < 30:
                self.test_info_average.append([2*0.5*i, 0.5*i/2, 0.5*i, 0.5*i])
            else:
                self.test_info_average.append([2*(14.5+1*(i-29)), (14.5+1*(i-29))/2, 14.5+1*(i-29), 14.5+1*(i-29)])

        #test calculation for approved values
        for entry, average in zip(self.test_info_numbers, self.test_info_average):
           self.correct_IP_Node.info = entry 
           self.assertAlmostEqual(self.correct_IP_Node._avg_info["cpu"], average[0], 1)
           self.assertAlmostEqual(self.correct_IP_Node._avg_info["memory"], average[1], 1) 
           self.assertAlmostEqual(self.correct_IP_Node._avg_info["disk"], average[2], 1) 
           self.assertAlmostEqual(self.correct_IP_Node._avg_info["swap"], average[3], 1) 
        #test calculation for wrong values
        with self.assertRaises(RuntimeError):
            self.correct_IP_Node.info = [1,2,3]
        with self.assertRaises(AttributeError):
            self.correct_IP_Node.info = [1,2,"ThisIsNotANumber", 4]
        with self.assertRaises(TypeError):
            self.correct_IP_Node.info = "asasd"

    def test_add_job(self):
        self.correct_IP_Node.max_jobs = 4
        #Adding 4 jobs and flushing them
        self.correct_IP_Node.add_jobs(self.Job_list_4)
        for job in self.correct_IP_Node.jobs:
            self.assertIn(job , self.Job_list_4)
            self.assertEqual(job.allocated, self.correct_IP_Node)
        self.correct_IP_Node.flush()
        
        #Adding 5 jobs
        with self.assertRaises(RuntimeError):
            self.correct_IP_Node.add_jobs(self.Job_list_5)

        #Adding somthing which is no BaseJob
        with self.assertRaises(RuntimeError):
            self.correct_IP_Node.add_jobs("TiHsiSaBasEJob")

    def test_flush_jobs(self):
        self.correct_IP_Node.max_jobs = 4
        #Adding 4 jobs and flushing them
        self.correct_IP_Node.add_jobs(self.Job_list_4)
        flushed = sorted(self.correct_IP_Node.flush(), key = lambda x: x.id)
        self.assertEqual(flushed, self.Job_list_4)
        self.assertEqual(len(self.correct_IP_Node.jobs), 0)

    def test_open_close_Node(self):
        self.correct_IP_Node.max_jobs = 4
        #Adding 4 jobs and flushing them
        self.correct_IP_Node.add_jobs(self.Job_list_4)
        self.assertEqual(len(self.correct_IP_Node.jobs), 4)
        self.assertEqual(self.correct_IP_Node.active, False)
        self.correct_IP_Node.open()
        self.assertEqual(self.correct_IP_Node.active, True)
        self.correct_IP_Node.close()
        self.assertEqual(self.correct_IP_Node.active, False)
        self.assertEqual(len(self.correct_IP_Node.jobs), 0)

    def test_getting_batman_info(self):
        batman_txt = """[B.A.T.M.A.N. adv 2018.3, MainIF/MAC: wlan0/b8:27:eb:e0:84:ce (bat0/ae:19:4f:16:ae:c1 BATMAN_IV)]
                            Originator        last-seen (#/255) Nexthop           [outgoingIF]
                            b8:27:eb:9b:64:78    0.820s   ( 85) b8:27:eb:4b:c7:04 [     wlan0]
                            b8:27:eb:9b:64:78    0.820s   (  0) b8:27:eb:3e:0b:bc [     wlan0]
                          * b8:27:eb:9b:64:78    0.820s   (144) b8:27:eb:9b:64:78 [     wlan0]
                            b8:27:eb:4b:c7:04    0.630s   (188) b8:27:eb:3e:0b:bc [     wlan0]
                            b8:27:eb:4b:c7:04    0.630s   (109) b8:27:eb:9b:64:78 [     wlan0]
                          * b8:27:eb:4b:c7:04    0.630s   (247) b8:27:eb:4b:c7:04 [     wlan0]
                            b8:27:eb:3e:0b:bc    0.150s   (175) b8:27:eb:4b:c7:04 [     wlan0]
                            b8:27:eb:3e:0b:bc    0.150s   ( 79) b8:27:eb:9b:64:78 [     wlan0]
                          * b8:27:eb:3e:0b:bc    0.150s   (255) b8:27:eb:3e:0b:bc [     wlan0]"""
        with open("bat.txt", "w") as f:
            f.write(batman_txt)
        mac_address = ["b8:27:eb:9b:64:78","b8:27:eb:3e:0b:bc","b8:27:eb:4b:c7:04" ]
        self.correct_IP_Node.batman_info()
        self.assertEqual(len(self.correct_IP_Node.routing_table), 3)
        for entry in self.correct_IP_Node.routing_table:
            self.assertIn(entry["mac"], mac_address)
            self.assertLess(int(entry["TQ"]), 256)
            self.assertGreaterEqual(int(entry["TQ"]), 0)
        os.remove("bat.txt")
        with open("bat.txt", "w") as f:
            f.write("Error")
        self.correct_IP_Node.batman_info()
        for entry in self.correct_IP_Node.routing_table:
            self.assertIsNone(entry["mac"])
            self.assertEqual(int(entry["TQ"]), 255)

    def test_add_routing_table(self):
        with self.assertRaises(TypeError):
            self.correct_IP_Node.routing_table = ""
        with self.assertRaises(KeyError):
            self.correct_IP_Node.routing_table = {"mac": "as", "NotTQ": "what"}
        with self.assertRaises(KeyError):
            self.correct_IP_Node.routing_table = {"IP": "as", "TQ": "234"}
        self.correct_IP_Node.routing_table = {"mac": "MACADRR", "TQ": "234"}
        self.assertEqual(self.correct_IP_Node.routing_table[0]["mac"], "MACADRR")
        self.assertEqual(self.correct_IP_Node.routing_table[0]["TQ"], "234")


    
