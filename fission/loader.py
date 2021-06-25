import csv
import logging

from lxml import objectify

from fission.core.groups import BaseGroup
from fission.core.jobs import DynamicMARVELOJob
from fission.core.nodes import BaseNode
from fission.core.pipes import LoaderPipe

logger = logging.getLogger(__name__)


class XMLLoader():
    def __init__(self, ip="pi_id", executable="executable", dependencies="path",
                 input="input", output="output", pipe_id="pipe_id",
                 parameter_tag="parameter", parameter="param",
                 block_size="block_size", block_count="block_count"):
        self.ip = ip
        self.executable = executable
        self.dependencies = dependencies
        self.input = input
        self.output = output
        self.pipe_id = pipe_id
        self.parameter_tag = parameter_tag
        self.parameter = parameter
        self.block_size = block_size
        self.block_count = block_count

    def load(self, xml_file):
        """Read XML file and generate according network

            Arguments:
                xml_file {str} -- path to xml file

            Return:
                bool -- Whether parsing succeded
            """
        print(f"Reading XML file from {xml_file}")

        with open(xml_file, "r") as f:
            root = f.read()
        root = objectify.fromstring(root)

        jobs = []
        nodes = []

        # loop through executables
        for node in root.getchildren():
            ip = node.get(self.ip)
            job_buffer = []
            for p in node.getchildren():
                inputs = []
                outputs = []
                parameters = []
                # get name of executable
                executable = p.get(self.executable)
                # get path
                path = p.get(self.dependencies)

                # loop through parameters (input/output pipes and additional params)
                for atom in p.getchildren():

                    # collect input pipes
                    if(atom.tag == self.input):
                        pipe = LoaderPipe(int(atom.get(self.pipe_id)))
                        if not atom.get(self.block_size):
                            pipe.block_size = 1
                        else:
                            pipe.block_size = int(atom.get(self.block_size))
                        count = atom.get(self.block_count)
                        if count:
                            pipe.block_count = int(count)
                        else:
                            pipe.block_count = 1
                        inputs.append(pipe)
                    # collect output pipes
                    if(atom.tag == self.output):
                        pipe = LoaderPipe(int(atom.get(self.pipe_id)))
                        if not atom.get(self.block_size):
                            pipe.block_size = 1
                        else:
                            print(self.block_size)
                            print(type(self.block_size))
                            pipe.block_size = int(atom.get(self.block_size))
                        count = atom.get(self.block_count)
                        if count:
                            pipe.block_count = int(count)
                        else:
                            pipe.block_count = 1
                        outputs.append(pipe)

                    # collect parameter
                    if(atom.tag == self.parameter_tag):
                        param = atom.get(self.parameter)
                        parameters.append(param)

                parameters = " ".join(parameters)
                job = DynamicMARVELOJob(path, executable,
                                        parameters, inputs=inputs, outputs=outputs)

                jobs.append(job)
                job_buffer.append(job)

            node = BaseNode(ip)
            # print(job_buffer)
            node.max_jobs = len(job_buffer)
            node.add_jobs(job_buffer)
            nodes.append(node)

        return nodes, jobs


class CSVLoader():
    def load_nodes(self, csv_path):
        """Try reading nodes from csv. Does not add any nodes on error.

        Arguments:
            csv_path {str} -- csv path
        """
        rows = []

        with open(csv_path, newline='') as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            for row in reader:
                rows.append(row)

        all_nodes = []
        for n, node in enumerate(rows):
            try:
                name = node[0].strip()
                ip = node[1].strip()
                node = BaseNode(ip, name=name)

                node.GROUPS = node[2:]

                all_nodes.append(node)

            except IndexError:
                raise RuntimeError(
                    f"Row {n} in file {csv_path} must at least define column 'name' and 'ip'")

        return all_nodes
