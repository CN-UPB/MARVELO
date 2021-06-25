import struct
import pytest
import queue
import fission.remote.synchronization as sync
import fission.core.base as base
import os


@pytest.fixture
#Creating Fifos
def pipes_root_dir(tmpdir):
    os.makedirs(tmpdir/"fifo/1", exist_ok=True)
    path = tmpdir/"fifo/1"
    for i in range(1,11):
        os.mkfifo(f"{path}/{i}.fifo") 
    return tmpdir

@pytest.fixture
#Creating pipes
def pipes():
    pipes = []
    for i in range(1,11):
        a = base.BasePipe(i)
        a.BLOCK_SIZE = 16
        pipes.append(a)
    yield pipes
    base.reset()

@pytest.fixture
#create jobs only with outputs and without inputs
def job_no_input(pipes):
    job = base.BaseJob(inputs=[], outputs=pipes)
    yield job
    base.reset()

@pytest.fixture
#create Jobs with inputs and outputs
def job_with_input(pipes):
    input_pipes = []
    for i in range(12,15):
        input_pipes.append(base.BasePipe(i))
    job = base.BaseJob(inputs=input_pipes, outputs=pipes)
    yield job
    base.reset()

        
@pytest.fixture
#Create Outputqueue
def outqueue():
    outqueues = []
    for i in range(10):
        outqueues.append(queue.Queue())
    return outqueues

@pytest.fixture
#create connection queue
def connect_queue(fission_queue):
    connection_queue = fission_queue
    for i in range(20):
        connection_queue.put(sync.Packet(struct.pack("!Q",i) + struct.pack('!B', int('10100000', base=2))))
    return connection_queue



def test_source_job(pipes_root_dir,job_no_input,outqueue,connect_queue):
    job_no_input.HEAD = True

    rst = queue.Queue()
    thread = sync.SendBlock(pipes_root_dir,job_no_input,outqueue,connect_queue,rst)

    pipes = []
    for i in range(1,11):
        pipes.append(open(f"{pipes_root_dir}/fifo/1/{i}.fifo", "wb", 0))

    #Writing into pipes
    for pipe in pipes:
        for i in range(0,9):
            if job_no_input.HEAD:
                pipe.write(struct.pack("!QQ", 2048, 100000) + struct.pack('!B', int('11100000', base=2)))
            else:
                pipe.write(struct.pack("!QQ", 2048, 100000))

          
    thread.start()

    for q in outqueue:
        for i in range(1,10):
            b = q.get()
            if job_no_input.HEAD:
                assert b.full_data == struct.pack("!Q", i) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
            else:    
                assert b.full_data == struct.pack("!Q", i) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)

    thread.kill()


def test_normal_job(pipes_root_dir,job_with_input,outqueue,connect_queue):

    job_with_input.HEAD = True


    thread = sync.SendBlock(pipes_root_dir, job_with_input, outqueue, connect_queue)

    pipes = []

    for i in range(1,11):
        pipes.append(open(f"{pipes_root_dir}/{i}.fifo", "wb", 0))

    for pipe in pipes:
        for i in range(20):
            if job_with_input.HEAD:
                #RST Flag of Joboutput-Head is set, but Head from Connection-Queue is not set
                pipe.write(struct.pack("!QQ",2048,100000) + struct.pack('!B', int('11100000', base=2)))
            else:
                pipe.write(struct.pack("!QQ", 2048, 100000))

    thread.start()

    for q in outqueue:
        for i in range(10):
            c = q.get()
            if job_with_input.HEAD:   
            #Rst Flag shouldnt be set anymore
                assert c.full_data == struct.pack("!Q",i) + struct.pack('!B',int('10100000',base=2)) + struct.pack("!QQ", 2048,100000)
            else:
                assert c.full_data == struct.pack("!Q", i) + struct.pack('!B', int('10100000', base=2)) + struct.pack("!QQ", 2048, 100000)

    thread.kill()



def test_reset(pipes_root_dir,job_no_input,outqueue,connect_queue):
    job_no_input.HEAD = False

    thread = sync.SendBlock(pipes_root_dir,job_no_input,outqueue,connect_queue,daemon=True)

    pipes = []
    for i in range(1,11):
        pipes.append(open(f"{pipes_root_dir}/{i}.fifo", "wb", 0))

    #Writing into pipes
    for pipe in pipes:
        for i in range(0,10):
            if job_no_input.HEAD:
                pipe.write(struct.pack("!QQ", 2048, 100000) + struct.pack('!B', int('11100000', base=2)))
            else:
                pipe.write(struct.pack("!QQ", 2048, 100000))

    thread.start()

    while True:
        if thread.source_sqn == 5:
            thread.command_rst.put(True)
            break


    for q in outqueue:
        for i in range(0,2):
            if job_no_input.HEAD:
                if i > 0:
                    assert q.get().full_data == struct.pack("!Q", 1) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 2) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 3) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 4) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 5) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                else:
                    assert q.get().full_data == struct.pack("!Q", 1) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 2) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 3) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 4) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 5) + struct.pack('!B', int('11100000', base=2)) + struct.pack("!QQ", 2048, 100000)
            else:
                if i > 0:    
                    assert q.get().full_data == struct.pack("!Q", 1) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 2) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 3) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 4) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 5) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                else:
                    assert q.get().full_data == struct.pack("!Q", 1) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 2) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 3) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 4) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)
                    assert q.get().full_data == struct.pack("!Q", 5) + struct.pack("!B", 0) + struct.pack("!QQ", 2048, 100000)



    






            




        

            




        







    





        







    


































