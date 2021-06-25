import socket
import time
import pytest
from fission.remote.synchronization import InputServer

# def test_multiple_connections(tcp_sockets, fission_queue, fission_pipe, fission_dummy):
#     fission_pipe._destination = 'localhost'
#     fission_pipe.BLOCK_SIZE = 8
#     thread = InputServer(fission_pipe, fission_queue, port_offset=2000, daemon=True)
#     thread.start()
#     start_sqn = fission_dummy.sqn + 1
#     for s in tcp_sockets(100):
#         fission_dummy._sqn += 1
#         s.connect(('localhost', 2000 + fission_pipe.id))
#         s.send(fission_dummy.full_data)
#         # add little sleep so threads dont overlap
#         time.sleep(.05)
    
    
#     for i in range(100):
#         packet = fission_queue.get(timeout=1)
#         print(packet)
#         assert packet.sqn == (start_sqn + i)
    
#     thread.socket.close()
