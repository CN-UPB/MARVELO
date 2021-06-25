import pytest
from fission.core.jobs import Head


#Create Head
@pytest.fixture
def head():
    a = Head(12,1)
    return a

def test_head_size(head):
    assert head.head_size == 1

    #Add 1 Byte
    head.head_size = 1 

    assert head.head_size == 2
    assert head.head == 3072

    head.head_size = -1
    assert head.head_size == 1
    assert head.head == 12

    head.head_size = -4
    assert head.head_size == 1
    assert head.head == 12


def test_head_slicing(head):  

    a = head[0:7:1]
    assert a == Head(6, len(head)) == 6

    a = head[0:3:1]
    assert a == Head(0, len(head)) == 0

    a = head[0:7:2]
    assert a == Head(2, len(head)) == 2

    a = head[5::]
    assert a == Head(4, len(head)) == 4

    a = head[::-1]
    assert a == Head(48, len(head)) == 48

    a = head[-2:-8:-2]
    assert a == Head(2, len(head)) == 2
    
def test_indexing(head):
    
    b = head[0]
    assert b == False

    b = head[5]
    assert b == True

    b = head[-1]
    assert b == False

    b = head[-3]
    assert b == True

    b = head[-4]
    assert b == True

    b = head[-5]
    assert b == False

    b = head[-8]
    assert b == False


def test_setitem(head):

    head[-8] = 1
    assert head.head == 140

    head[7] = 1
    assert head.head == 141

    head[-3] = 0
    assert head.head == 137





    

