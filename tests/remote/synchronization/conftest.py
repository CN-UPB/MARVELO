import queue
import socket
import threading

import pytest
from fission.remote.synchronization import Packet

@pytest.fixture
def fission_dummy():
    return Packet.get_dummy(1024, 8)

@pytest.fixture
def tcp_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    yield s
    s.close()

@pytest.fixture
def tcp_sockets():
    sockets = []
    def _sockets(num):
        for _ in range(num):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sockets.append(s)
        return sockets
    yield _sockets
    
    for s in sockets:
        s.close()

@pytest.fixture
def tcp_connected_sockets():
    # setup server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 2000))
    server_socket.listen(5)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    threading.Thread(target=client_socket.connect, args=(('localhost', 2000),), daemon=True).start()

    connection = server_socket.accept()

    yield (client_socket, connection[0])
    connection[0].close()
    server_socket.close()
    client_socket.close()

@pytest.fixture
def fission_queue():
    """Retuns a queue.
    """
    return queue.Queue()


@pytest.fixture
def fission_queues():
    """Returns a function which returns given number of Queues with optional size.
    """
    def _queues(num, size=-1):
        return [queue.Queue(size) for i in range(num)]
    return _queues
