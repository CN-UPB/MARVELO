import unittest
import os
import shutil

from dispy import logger as dispy_logger
import fission.core.base as base
from fission.core.nodes import BaseNode
from fission.core.jobs import BaseJob

dispy_logger.setLevel(dispy_logger.ERROR)

class TestJob(unittest.TestCase):

    def setUp(self):
        self.Node1 = BaseNode("192.168.4.2")
        self.Node2 = BaseNode("192.168.4.3")
        self.Job = BaseJob()
        self.Job2 = BaseJob()

    def tearDown(self):
        base.NODES =  {}
        base.JOBS = {}

    def test_allocate(self):
        self.assertEqual(self.Job.allocated, None)
        self.assertEqual(self.Job.status, self.Job.STOPPED)
        self.Job.allocate(self.Node1)
        with self.assertRaises(RuntimeError):
            self.Job.allocate(self.Node2)
        with self.assertRaises(RuntimeError):
            self.Job2.allocate("NotANode")
        self.assertEqual(self.Job.allocated, self.Node1)

    def test_deallocate(self):
        self.Job.allocate(self.Node1)
        self.assertEqual(self.Job.allocated, self.Node1)
        self.Job.deallocate()
        self.assertEqual(self.Job.allocated, None)
        self.Job.status = self.Job.RUNNING
        self.Job.deallocate()
        self.assertEqual(self.Job.status, self.Job.STOPPED)
        self.Job.status = self.Job.FINISHED
        self.Job.deallocate()
        self.assertEqual(self.Job.status, self.Job.FINISHED)