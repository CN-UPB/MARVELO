import struct
import unittest
import pytest
import queue
import fission.core.base as base
import random
import time
 

import fission.remote.synchronization as sync


class TestSQN_Checker(unittest.TestCase):
    def setUp(self):
        self.inqueuelist = [queue.Queue(-1), queue.Queue(-1), queue.Queue(-1)]
        self.copy_inqueuelist = [queue.Queue(-1), queue.Queue(-1), queue.Queue(-1)]
        self.outqueuelist = [queue.Queue(-1), queue.Queue(-1), queue.Queue(-1)]
        self.queue_for_output = queue.Queue(-1)
        self.small_connection_queue = queue.Queue(10)
        self.pipes = [base.BasePipe(1),base.BasePipe(2),base.BasePipe(3)]
        self.Testchecker = sync.SQN_Checker(self.inqueuelist,self.outqueuelist,self.pipes,self.queue_for_output,daemon=True)
        self.Testchecker_prev_mode = sync.SQN_Checker(self.inqueuelist,self.outqueuelist,self.pipes,self.queue_for_output,dummy_mode="prev",daemon=True)
        self.Testchecker_small_connection_queue = sync.SQN_Checker(self.inqueuelist,self.outqueuelist,self.pipes,self.small_connection_queue,daemon=True)

    def tearDown(self):
        base.PIPES = {}

    def test_head_join(self):
        self.Testchecker.head_join(128)
        self.Testchecker.head_join(1<<7)
        self.assertEqual(self.Testchecker.outputhead, 128)
        self.Testchecker.head_join(0)
        self.assertEqual(self.Testchecker.outputhead, 128)
        self.Testchecker.head_join(128 + 24)
        self.assertEqual(self.Testchecker.outputhead, 152)

    def test_run_no_packet_lost(self):
        for i in range(1,100):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.Testchecker.start()
        for _ in range(1,100):
            self.assertEqual(self.copy_inqueuelist[0].get().full_data,self.outqueuelist[0].get().full_data)
            self.assertEqual(self.copy_inqueuelist[1].get().full_data,self.outqueuelist[1].get().full_data)
            self.assertEqual(self.copy_inqueuelist[2].get().full_data,self.outqueuelist[2].get().full_data)
        for i in self.outqueuelist:
            self.assertTrue(i.empty())

    def test_run_10percent_packet_lost(self):
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        random.seed(7)
        for i in range(2,100):
            if not(random.random()*100 < 10): 
                self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
                self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            if not(random.random()*100 < 10):
                self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
                self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            if not(random.random()*100 < 10):
                self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
                self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.Testchecker.start()
        q = None
        for j in range(3):
            for i in range(1,99):
                q = self.outqueuelist[j].get()
                if q.head == 128:
                    self.assertEqual(sync.Packet.get_dummy(i,self.pipes[j].BLOCK_SIZE).full_data ,q.full_data)
                else:
                    self.assertEqual(self.copy_inqueuelist[j].get().full_data ,q.full_data)


    def test_run_50percent_packet_lost(self):
        random.seed(5)
        for i in range(1,100):
            if not(random.random()*100 < 50): 
                self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
                self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            if not(random.random()*100 < 50):
                self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
                self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            if not(random.random()*100 < 50):
                self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
                self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
        self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
        self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",100) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        
        self.Testchecker.start()

        
        q = None
        for j in range(3):
            for i in range(1,101):
                q = self.outqueuelist[j].get()
                if q.head == 128:
                    self.assertEqual(sync.Packet.get_dummy(i,self.pipes[j].BLOCK_SIZE).full_data , q.full_data)
                else:
                    self.assertEqual(self.copy_inqueuelist[j].get().full_data , q.full_data)
 
                

    def test_run_connectionqueue_change_first_four_packets(self):
        random.seed(5)
        for i in range(1,100):
            if not(random.random()*100 < 50): 
                self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
                self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            if not(random.random()*100 < 50):
                self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
                self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            if not(random.random()*100 < 50):
                self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
                self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.Testchecker.start()
        self.assertAlmostEqual(self.queue_for_output.get().head, 0)
        self.assertAlmostEqual(self.queue_for_output.get().head, 0)
        self.assertAlmostEqual(self.queue_for_output.get().head, 128)
        self.assertAlmostEqual(self.queue_for_output.get().head, 128)

    def test_run_rst_flag_at_same_packet_number(self):
        #first ten packets normal, until sqn=9
        for i in range(1,10):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            
        
        # 11. packet is reset packet, packet with sqn = 10
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        

        # packets 12 - 21 normal again, sqn from 1 - 10
        for i in range(2,11):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            
        
        self.Testchecker.start()

        for i in self.outqueuelist:
            for j in range(1,11):
                self.assertEqual(i.get().sqn, j)
            for j in range(1,11):
                self.assertEqual(i.get().sqn, j)

    def test_run_rst_flag_at_different_packet_number(self):
        #first ten packets normal, until sqn=9
        for i in range(1,10):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            
        
        # 11. packet is reset packet by input pipe 0, packet with sqn = 10
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",10) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",10) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        

        # packets 12 - 21 normal again, sqn from 1 - 10
        for i in range(2, 10):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            
        
        self.Testchecker.start()

        for i in self.outqueuelist:
            for j in range(1,12):
                self.assertEqual(i.get().sqn, j)
            for j in range(1,10):
                self.assertEqual(i.get().sqn, j)

    def test_run_dummy_mode_prev(self):
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        for i in range(2,10):
            if i != 3:
                self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
                self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            if i != 5:
                self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
                self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            if i != 7:
                self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
                self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))

        self.Testchecker_prev_mode.start()
        
        for i in range(1,10):
            if i != 3:
                self.assertEqual(self.copy_inqueuelist[0].get().full_data, self.outqueuelist[0].get().full_data)
            else:
                self.assertEqual(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 128)+ struct.pack("!Q",1234)).full_data, self.outqueuelist[0].get().full_data)
            if i != 5:
                self.assertEqual(self.copy_inqueuelist[1].get().full_data, self.outqueuelist[1].get().full_data)
            else:
                self.assertEqual(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 128)+ struct.pack("!Q",12345)).full_data, self.outqueuelist[1].get().full_data)
            if i != 7:
                self.assertEqual(self.copy_inqueuelist[2].get().full_data, self.outqueuelist[2].get().full_data)
            else:
                self.assertEqual(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 128)+ struct.pack("!Q",123456)).full_data, self.outqueuelist[2].get().full_data)

    def test_push_dummy_error(self):
        with self.assertRaises(ValueError):
            self.Testchecker.dummy_in_outqueue(0,0,"test",0)

    def test_run_connectionqueue_full(self):
        for i in range(1,15):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))

        self.Testchecker_small_connection_queue.start()

        for i in range(1,5):
            self.copy_inqueuelist[0].get()
            self.copy_inqueuelist[1].get()
            self.copy_inqueuelist[2].get()

        for i in range(10):
            self.assertEqual(self.copy_inqueuelist[0].get().full_data, self.outqueuelist[0].get().full_data)
            self.assertEqual(self.copy_inqueuelist[1].get().full_data, self.outqueuelist[1].get().full_data)
            self.assertEqual(self.copy_inqueuelist[2].get().full_data, self.outqueuelist[2].get().full_data)

    
    def test_run_2_3_1_packet_per_pipe(self):
        self.pipes[0].BLOCK_COUNT = 2
        self.pipes[0].BLOCK_COUNT = 3
        self.pipes[0].BLOCK_COUNT = 1
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        for i in range(2,100):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.Testchecker.start()
        for i in range(len(self.pipes)):
            for j in range(self.pipes[i].BLOCK_COUNT):
                for x in range(20):
                    q = self.outqueuelist[i].get()
                    if q.head == 128:
                        self.assertEqual(sync.Packet.get_dummy(x,self.pipes[i].BLOCK_SIZE).full_data , q.full_data)
                    else:
                        self.assertEqual(self.copy_inqueuelist[i].get().full_data , q.full_data)

    

    def test_run_connection_queue_reset_check(self):
        self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",1234)))
        self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",12345)))
        self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",1) + struct.pack("!B", 64)+ struct.pack("!Q",123456)))
        for i in range(2,100):
            self.inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
            self.copy_inqueuelist[0].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",1234)))
            self.copy_inqueuelist[1].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",12345)))
            self.copy_inqueuelist[2].put(sync.Packet(struct.pack("!Q",i) + struct.pack("!B", 0)+ struct.pack("!Q",123456)))
        self.Testchecker.start()
        self.assertEqual(self.Testchecker.connection_queue.get().head, 64)
        for _ in range(2,100):
            self.assertEqual(self.Testchecker.connection_queue.get().head, 0) 
        
