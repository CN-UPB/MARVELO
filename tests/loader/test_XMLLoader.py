import os
from distutils import dir_util
import pytest

from fission.loader import XMLLoader
import fission.core.base as base

@pytest.fixture
def xml_loader():
    yield XMLLoader(ip="ip")
    base.reset()

@pytest.fixture()
def xml_dir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir

def test_valid_xml(xml_loader, xml_dir):
    valid_file = xml_dir/"network_valid.xml"
    nodes, jobs = xml_loader.load(valid_file)
    for i, node in enumerate(nodes, 1):
        assert node.ip == f"192.168.4.{i}" 
    
    # check number of assigned jobs
    assert all([len(n.jobs)==2 for n in nodes[:2]])
    assert all([len(n.jobs)==1 for n in nodes[2:]])

    for i, j in enumerate(jobs, 1):
        # check jobs
        assert j.DEPENDENCIES == f"{i}"
        # job 5 has no params
        if i != 5:
            assert j.PARAMETERS == f"param{i}"
        assert j.EXECUTABLE == f"exe{i}"
    
    for id, p in base.PIPES.items():
        # Check Pipes
        if id == 1:
            assert p.block_count == 5
        else:
            assert p.block_count == 1
        
        assert p.block_size == id*10

def test_pipe_with_multiple_output(xml_loader, xml_dir):
    invalid_file = xml_dir/"network_multi_destination.xml"
    with pytest.raises(RuntimeError) as excinfo:
        xml_loader.load(invalid_file)
    
    assert "Source of pipe 1 was defined multiple times." in str(excinfo.value)

def test_pipe_with_multiple_input(xml_loader, xml_dir):
    invalid_file = xml_dir/"network_multi_source.xml"
    with pytest.raises(RuntimeError) as excinfo:
        xml_loader.load(invalid_file)
    
    assert "Destination of pipe 1 was defined multiple times." in str(excinfo.value)

def test_pipe_with_multiple_block_sizes(xml_loader, xml_dir):
    print(base.PIPES)
    invalid_file = xml_dir/"network_different_block_size.xml"
    with pytest.raises(RuntimeError) as excinfo:
        xml_loader.load(invalid_file)
    
    assert "Multiple block sizes are set for pipe 1." in str(excinfo.value)

def test_pipe_with_multiple_block_counts(xml_loader, xml_dir):
    invalid_file = xml_dir/"network_different_block_count.xml"
    with pytest.raises(RuntimeError) as excinfo:
        xml_loader.load(invalid_file)
    
    assert "Multiple block counts are set for pipe 1." in str(excinfo.value)
