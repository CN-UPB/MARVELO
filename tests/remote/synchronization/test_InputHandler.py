import pytest
import struct
import time

from fission.remote.synchronization import InputHandler, Packet

# def test_packet_equals_sent_data(tcp_connected_sockets, fission_queue, fission_dummy):
#     sender, receiver = tcp_connected_sockets
#     size = 8 + 1 + 8
#     thread = InputHandler(receiver, size, fission_queue, daemon=True)

#     thread.start()
#     # call so thread retuns after receiving
#     thread.kill()
    
#     sender.send(fission_dummy.full_data)
    
#     received = fission_queue.get(5)

#     assert isinstance(received, type(fission_dummy))
#     assert fission_dummy.full_data == received.full_data



