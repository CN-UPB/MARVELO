import pytest
import os

from fission.remote.synchronization import ReadPipe, Packet


# def test_reading(tmpdir, fission_queue, fission_pipe):
#     fission_pipe.BLOCK_SIZE = 10

#     path = tmpdir/"fifo"
#     print(path)
#     os.mkfifo(path)
#     ReadPipe(path, fission_pipe, fission_queue, daemon=True).start()
#     with open(path, 'wb', 0) as f:
#         for i in range(50):
#             f.write(Packet.get_dummy(i, 10).full_data)

#     for i in range(50):
#         assert fission_queue.get(5).sqn == i
