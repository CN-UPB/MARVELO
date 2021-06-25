import pytest
import os

from fission.remote.synchronization import WritePipe, Packet

def test_writing(tmpdir, fission_queue, fission_pipe):
    fission_pipe.BLOCK_SIZE = 10

    path = tmpdir/"fifo"
    print(path)
    os.mkfifo(path)
    WritePipe(path, fission_pipe, fission_queue, daemon=True).start()
    for i in range(50):
        fission_queue.put(Packet.get_dummy(i, 10))
    with open(path, 'rb', 0) as f:
        for i in range(50):
            assert Packet(f.read(19)).sqn == i



