import queue
import socket
import pytest
import fission.remote.synchronization as sync
import fission.core.base as base
import struct
from fission.remote.synchronization import InputServer, Packet
import pickle
import os
import threading

@pytest.fixture
def pipes():
    a = []
    a.append(base.BasePipe(1))
    a[0].BLOCK_SIZE = 16
    yield a
    base.reset()


@pytest.fixture
def job_no_input(pipes):
    job = base.BaseJob(inputs=[],outputs=pipes)
    yield job
    base.reset()


@pytest.fixture
def sendqueue():

    outpqueue = []
    outpqueue.append(queue.Queue())
    outpqueue[0].put(Packet(struct.pack('!Q',1) + struct.pack('!B', 0) + struct.pack('!QQ',2048,10000)))
    return outpqueue

@pytest.fixture
def inpqueue():
    inp = []
    inp.append(queue.Queue())
    return inp

@pytest.fixture
def result():

    res = []
    res.append(queue.Queue())
    res[0].put(Packet(struct.pack('!Q',1) + struct.pack('!B', 0) + struct.pack('!QQ',2048,10000)))
    return res


def test_send(job_no_input, sendqueue):
    
    threads = []


    for pipe, queue in zip(job_no_input.outputs, sendqueue):
       threads.append(sync.SendSocket('localhost', pipe.id + 2000, queue, daemon=True))


    for thread in threads:
        thread.start()

    
    for pipe, queue in zip(job_no_input.outputs, sendqueue):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(5)
        s.bind(('localhost', pipe.id + 2000))
        s.listen(2)

        while True:
            try:
                conn = s.accept()
                break
            except socket.error:
                pass

        file = conn[0].makefile("rb")
        loader = pickle.Unpickler(file)
        packet = loader.load()

        assert packet.sqn == 1
        assert packet.head == 0b0
        assert packet.data == struct.pack('!QQ',2048,10000)
    
  
    for thread in threads:
        thread.kill()



    

    

    

    























