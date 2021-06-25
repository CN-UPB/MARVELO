from fission.core.jobs import MARVELOJob

def Spark3Job(MARVELOJob):
    EXECUTABLE = "./spark3"
    DEPENDENCIES = "source/spark3/"

    DEFAULT_NODE = "192.168.4.5"

    GROUPS = "SPARK3"

    def __init__(self, param, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PARAMETERS = param