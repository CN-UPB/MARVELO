from ctypes import cdll
import ctypes
import numpy

# load dynamic library from file (compiled by make)
lib = cdll.LoadLibrary('./cpplib/libpipeinterface.so')


class Pipeinterface(object):
    MAX_BUFFER_SIZE = 20000
    DataRxBuffer = ctypes.create_string_buffer(MAX_BUFFER_SIZE)  # memory for raw data
    DataType = numpy.float32

    def __init__(self, instance_name: str, data_size: int):
        """
        Distributed Data Network (DDN) client class for communication
        with network soundcards support by the dynamic libpipeinterface.so class.
        Constructor requires parameters instance_name and pipe_name.
        instance_name is used to identify the local node,
        the pipe_name is an upcoming feature to filter nodes by
        network identification names.

        :param instance_name: Name of pipeinterface instance (our nodes name)
        :param pipe_name: Name of Network (use "ans")
        """
        lib.pipeinterface_GetDataWithTimeout.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int
        ]
        lib.pipeinterface_GetDataWithTimeout.restype = ctypes.c_int

        lib.pipeinterface_new.argtypes = [ctypes.c_char_p, ctypes.c_int]
        lib.pipeinterface_new.restype = ctypes.c_void_p
        self.obj = lib.pipeinterface_new(instance_name.encode(), data_size)

    def set_data_type(self, new_data_type):
        """
        Use this mehtod to define the data_type to be send via the network.
        Standard is int32, as served by the network soundcards
        :param new_data_type: numpy datatype, e.g. numpy.int32
        :return: nothing
        """
        self.DataType = new_data_type

    def get_data_with_timeout(
            self, data, time_to_wait
    ):
        """
        Method to receive data from the nodes stack. All data received by the
        node is stored on a stack and dropped if the stack is exceeding a limit.
        So after requesting data via pipeinterface.SendCommandWithTimeout(MSG_TYPE=4) the
        far end node will start sending data to us. This data is stored on the
        stack and available only through this method. SenderName, Data and
        PackNum are return values (call by reference), but we have to
        organize/allocate the memory!
        :param sender_name: Returned value - the far end nodes name
        :param data: Returned values - the data received from the far end node
        :param packet_number: Returned value - packet number of the data
        :param time_to_wait: Time to wait for data (no waiting if = 0 )
        :return: Size of data served from the stack, zero if no data
        """
        return lib.pipeinterface_GetDataWithTimeout(
            self.obj, data, time_to_wait
        )


    def get_data(self, time_to_wait):
        """
        Get data from buffer stack of pthread lib running in background
        :param time_to_wait: time to wait for a data packet in seconds
        :return: dictionary containing data and additional information
        """
        data_size = 0
        buffer_size = self.get_data_with_timeout(
            self.DataRxBuffer, time_to_wait
        )
        data = numpy.frombuffer(self.DataRxBuffer[0:buffer_size], dtype=self.DataType)
        if buffer_size > 0:
            data_size = data.size
        return {"Data": data, "Size": data_size}

