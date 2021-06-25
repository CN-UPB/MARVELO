import pytest
import struct

from fission.remote.synchronization import Packet


@pytest.fixture
def sqn():
    return struct.pack("!Q", 2)


@pytest.fixture
def head():
    return struct.pack('!B', int('11100000', base=2))


@pytest.fixture
def data():
    return struct.pack("!QQ", 2048, 100000)


@pytest.fixture
def raw_data(sqn, head, data):
    return sqn + head + data


@pytest.fixture
def packet(raw_data):
    return Packet(raw_data)


def test_property_full_data(packet, raw_data):
    assert packet.full_data == raw_data


def test_property_data(packet, data):
    assert packet.data == data


def test_property_head(packet, head):
    # test getter
    assert isinstance(packet.head, int)

    assert packet.head == int.from_bytes(head, byteorder='big')

    # test setter
    new_head = struct.pack("!B", 111)
    packet.head = new_head
    assert packet.head == 111

    new_head = 255
    packet.head = new_head
    assert packet.head == new_head


def test_property_corrupted(packet):
    assert True == packet.corrupted
    packet.corrupted = False
    assert False == packet.corrupted


def test_property_finished(packet):
    assert True == packet.finished
    packet.finished = False
    assert False == packet.finished


def test_property_rst(packet):
    assert True == packet.rst
    packet.rst = False
    assert False == packet.rst


def test_property_sqn(packet):
    assert packet.sqn == 2


def test_dummy_packet():
    # implicit test for Packet with no data, only sqn + head
    dummy = Packet.get_dummy(5, 0)

    assert dummy.sqn == 5
    assert len(dummy.data) == 0
    # check flags
    assert dummy.corrupted
    assert not dummy.finished
    assert not dummy.rst

    dummy = Packet.get_dummy(10, 1000)

    assert dummy.data == b'\0'*1000
