import json
import logging
import os
import queue
import socket
import socketserver
import struct
import threading
import time
import pickle

logger = logging.getLogger(__name__)


class Packet():
    def __init__(self, data, head_size=1, sqn_size=8):
        """Represent a block of data. Provides properties for:
        - full_data -- get the complete packet in bytes (read only)
        - data -- get the data of the packet in bytes (read only)
        - head -- get or set the packets head. Returns int for easy bitwise ops.
                  For setting the head both bytes and int are valid.
        - sqn -- get sqn as int (read only)
        - corrupted -- get or set corrupted flag
        - rst -- get or set reset flag
        - finished -- get or set finished flag

        In addition a classmethod (get_dummy) is provided. It is an easy interface
        for creating dummy packets.

        Arguments:
            data {bytes} -- Complete data block (including sqn and head)

        Keyword Arguments:
            head_size {int} -- head size in bytes(reserved for future use) (default: {1})
            sqn_size {int} -- sqn size in bytes (reserved for future use) (default: {8})
        """
        self._data = data[head_size+sqn_size:]
        self._head = int.from_bytes(
            data[sqn_size:head_size+sqn_size], byteorder='big')
        self._sqn = int.from_bytes(data[:sqn_size], byteorder='big')
        self.head_size = head_size
        self.sqn_size = sqn_size

    @property
    def full_data(self):
        return self.sqn.to_bytes(self.sqn_size, byteorder='big') + self.head.to_bytes(self.head_size, byteorder='big') + self.data

    @property
    def data(self):
        return self._data

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, value):
        if isinstance(value, bytes):
            if len(bytes(value)) == self.head_size:
                self._head = int.from_bytes(value, 'big')
            else:
                raise RuntimeError("Header has unexpected size.")
        elif isinstance(value, int):
            if value >= 2**(8*self.head_size):
                raise RuntimeError("Header has unexpected size.")
            self._head = value
        else:
            raise TypeError(f"Head is set by int or bytes, not {type(value)}")

    @property
    def sqn(self):
        return self._sqn

    @property
    def corrupted(self):
        return bool(self.head & (1 << (self.head_size*8-1)))

    @corrupted.setter
    def corrupted(self, corrupt):
        if corrupt:
            self.head = self.head | (1 << (self.head_size*8-1))
        else:
            self.head = self.head & ~(1 << (self.head_size*8-1))

    @property
    def rst(self):
        return bool(self.head & (1 << (self.head_size*8-2)))

    @rst.setter
    def rst(self, rst):
        if rst:
            self.head = self.head | (1 << (self.head_size*8-2))
        else:
            self.head = self.head & ~(1 << (self.head_size*8-2))

    @property
    def finished(self):
        return bool(self.head & (1 << (self.head_size*8-3)))

    @finished.setter
    def finished(self, finish):
        if finish:
            self.head = self.head | (1 << (self.head_size*8-3))
        else:
            self.head = self.head & ~(1 << (self.head_size*8-3))

    @classmethod
    def get_dummy(cls, sqn, block_size=0, p_data=None, head_size=1, sqn_size=8, **kwargs):
        sqn = sqn.to_bytes(sqn_size, 'big')
        head = int('10000000', 2).to_bytes(head_size, 'big')
        if p_data:
            data = p_data
        else:
            data = b'\0' * block_size
        obj = cls(sqn + head + data, **kwargs)

        return obj

    def __str__(self):
        return "Packet: SQN:{} HEAD:{} DATA:{} bytes".format(self.sqn, "{:0{padding}b}".format(self.head, padding=self.head_size*8), len(self.data))

    def __repr__(self):
        return str(self)


class SQN_Checker(threading.Thread):
    def __init__(self, inqueues, outqueues, pipes, connection_queue=None, finish_event=None, dummy_mode="zero", **kwargs):
        """Checks SQN of inputqueues and write them into outputqueues
        in case of missing blocks dummy-blocks are inserted

        Arguments:
            inqueues {list of queues} -- SQN of Packets in these Queues will be checked
            outqueues {list of queues} -- Packets and possible Dummy-Packets will be in these Queues after checking
            pipes {list of pipes} -- Inputpipes for id, BLOCK_SIZE, BLOCK_COUNT

        Keyword Arguments:
            connection_queue {queue} -- Queue for Output-SQN and Head of Job, None queue if end_node (default: {None})
            finish_event {threading.event} -- Event to stop the job, only at Sinkjob
            dummy_mode {"zero","prev"} -- data of dummy packet filled with zeroes or from previous packet
        """
        super().__init__(**kwargs)
        self.inqueues = inqueues
        self.outqueues = outqueues
        self.pipes = pipes
        self.data_len = [pipe.BLOCK_SIZE for pipe in pipes]
        self.block_count = [pipe.BLOCK_COUNT for pipe in pipes]
        self.head_size = pipes[0]._head_size
        self.datalist = [None for _ in range(len(inqueues))]
        self.prev_data = [None for _ in range(len(inqueues))]
        self.get_dummy_method = [hasattr(pipe, "get_dummy") for pipe in pipes]
        self.rstlist = [0 for _ in range(len(inqueues))]
        self.counter = 0
        self.connection_queue = connection_queue
        self.finish_event = finish_event
        self.outputhead = 0
        self.q = None
        self.dummy_mode = dummy_mode
        self.async_count = 0
        self.async_count_beginning = 0
        

    def run(self):

        for pipe in self.pipes:
            if pipe.ASYNC:
                self.async_count += 1

        for pipe in self.pipes:
            if pipe.ASYNC:
                self.async_count_beginning += 1
            else:
                break

        while True:

            for i in range(len(self.inqueues)):
                for j in range(self.block_count[i]):

                    if self.pipes[i].ASYNC:
                        continue

                    else:
                        if self.datalist[i]:

                            # if all inqueues had one reset flag the counter and reset list is set to 0 and the packets with
                            # sqn 1 start
                            if sum(self.rstlist) == (len(self.rstlist)-self.async_count) and i == self.async_count_beginning and j == 0:
                                self.counter = 1
                                self.packet_in_outqueue(index=i)
                                self.rstlist = [
                                    0 for _ in range(len(self.inqueues))]

                            # if packet in datalist has the right sqn it will be pushed in outqueue and deleted from datalist
                            # otherwise dummy is pushed in outqueue
                            else:

                                if self.datalist[i].sqn == self.block_count[i]*self.counter+j:
                                    self.packet_in_outqueue(index=i)

                                else:
                                    self.dummy_in_outqueue(
                                        i, j, self.datalist[i].sqn)

                        else:

                            # get new packet
                            self.q = self.inqueues[i].get()
                            # logger.debug(f"NEW PACKET@{self.pipes[i]}: {self.q}")

                            # counter == 0 only at the beginning
                            if self.counter == 0 and self.q.sqn == 1:
                                self.packet_in_outqueue(packet=self.q, index=i)

                                if i == (len(self.inqueues)-1):
                                    self.counter = 1

                            # if sqn is spawned new but with old pipe (so high sqn will appear next)
                            elif (self.counter == 0 and self.q.sqn != 1):
                                self.counter = self.q.sqn//self.block_count[i]
                                self.packet_in_outqueue(packet=self.q, index=i)

                            # if reset flag is set in q, dummy is pushed in outqueue and q is stored for later
                            elif ((self.q.head & (1 << 6)) and self.counter != 0):

                                if self.counter != 0:
                                    self.rstlist[i] = 1

                                self.datalist[i] = self.q
                                self.dummy_in_outqueue(
                                    i, j, self.q.sqn)

                            # if sqn from q is smaller than expected and no reset flag is set,
                            # q is thrown away and next packets are inspected until sqn is not smaller anymore
                            elif self.q.sqn < self.block_count[i]*self.counter+j:
                                # delete packets with smaller sqn than expected
                                while self.q.sqn < self.block_count[i]*self.counter+j:
                                    self.q = self.inqueues[i].get()

                                    # need to check reset flag again
                                    if (((self.q.head & (1 << 6)) or self.q.sqn == 1) and self.counter != 0) or (self.counter == 0 and i == len(self.inqueues) - 1 and self.q.sqn != 1):
                                        self.rstlist[i] = 1
                                        self.datalist[i] = self.q
                                        self.dummy_in_outqueue(
                                            i, j, self.q.sqn)
                                        break

                            # if sqn from q is greater than expected, dummy packet is pushed in outqueue
                            # q is put in datalist for later
                            elif self.q.sqn > self.block_count[i]*self.counter+j and self.counter != 0:
                                self.datalist[i] = self.q
                                self.dummy_in_outqueue(
                                    i, j, self.q.sqn)

                            # if q.sqn is right q is pushed in the outqueue
                            else:
                                self.packet_in_outqueue(packet=self.q, index=i)

            # connection queue exists when job is no ending job
            if self.connection_queue:

                # if connection_queue is full, old packets will be deleted from connection_queue and outputqueue
                if self.connection_queue.full():
                    self.connection_queue.get()
                    for p in range(len(self.inqueues)):
                        for _ in range(self.block_count[i]):
                            self.outqueues[p].get()

                # sqn & head is pushed to connection_queue, 8 for sqn_size
                self.connection_queue.put(
                    Packet(self.counter.to_bytes(8, 'big') + self.outputhead.to_bytes(self.head_size, 'big'),head_size=self.head_size))
                self.outputhead = 0

            # after every run counter is increased
            self.counter += 1

    def packet_in_outqueue(self, packet=None, index=None):
        """handed over packet or packet from datalist will be pushed in outqueue

        Keyword Arguments:
            packet {Packet} -- packet, which will be pushed in outqueue (default: {None})
            index {[type]} -- index to identify in which outqueue will be pushed (default: {None})

        Raises:
            RuntimeError: Error if no packet in datalist
            ValueError: function has to be called with minimum index parameter
        """
        if packet and index != None:
            self.outqueues[index].put(packet)
            self.prev_data[index] = packet.data
            self.head_join(packet.head)
        elif index != None:
            if not self.datalist[index]:
                raise RuntimeError(f"No packet in datalist for pipe: {index}")
            self.outqueues[index].put(self.datalist[index])
            self.prev_data[index] = self.datalist[index].data
            self.head_join(self.datalist[index].head)
            self.datalist[index] = None
        else:
            raise ValueError(f"No packet or index for pipe given")

    def dummy_in_outqueue(self, queue_index, run_index, given_sqn):
        """dummy packet will be pushed in outqueue

        Arguments:
            queue_index {int} -- index for outqueue and pipe
            run_index {int} -- index for run for right sqn (BLOCK_COUNT)
            mode {string} -- "prev" for previous data, "zero" for filling data with 0. Overridden to "prev" if 'PKL'
            given_sqn {int} -- for logger warning

        Raises:
            ValueError: wrong mode passed
        """
        if isinstance(self.data_len[queue_index], str):
            self.dummy_mode = "prev"

        # save counter if dummy pushed for the first paket
        old_counter = self.counter
        if self.counter == 0:
            self.counter = 1

        logger.warning(
            f"Make Dummy. Given SQN:{given_sqn}. Expected SQN:{self.block_count[queue_index]*self.counter+run_index}. For Pipe:{self.pipes[queue_index]}")

        if self.get_dummy_method[queue_index]:

            return_value = self.pipes[queue_index].get_dummy()
            if isinstance(return_value, bytes):
                if isinstance(self.data_len[queue_index], int):
                    if len(return_value) == self.data_len[queue_index]:
                        self.outqueues[queue_index].put(Packet.get_dummy(int(
                            self.block_count[queue_index])*self.counter+run_index, p_data=return_value))
                    else:
                        self.dummy_mode_in_outqueue(
                            queue_index, run_index, log=f"return of get_dummy from {self.pipes[queue_index]} does not match length of BLOCK_SIZE {self.data_len[queue_index]}! Dummy-mode {self.dummy_mode} used")
                else:
                    self.dummy_mode_in_outqueue(
                        queue_index, run_index, log=f"BLOCK_SIZE: {self.data_len[queue_index]} from {self.pipes[queue_index]} no integer. Dummy-mode {self.dummy_mode} used")
            else:
                self.dummy_mode_in_outqueue(
                    queue_index, run_index, log=f"return of get_dummy from {self.pipes[queue_index]} are not bytes! Dummy-mode {self.dummy_mode} used")
        else:
            self.dummy_mode_in_outqueue(queue_index, run_index)

        self.head_join(128)

        if old_counter == 0:
            self.counter = 0

    def dummy_mode_in_outqueue(self, queue_index, run_index, head_size=None, log=None):
        """Put Dummy in outqueue in mode 'zero' or 'prev'

        Arguments:
            queue_index {int} -- index for outqueue and pipe
            run_index {int} -- index for run for right sqn (BLOCK_COUNT)

        Keyword Arguments:
            log {string} -- string will be logged as a warning (default: {None})

        Raises:
            ValueError: wrong mode passed
        """
        if log:
            logger.warning(f"{log}")
        if self.dummy_mode == "zero":
            self.outqueues[queue_index].put(Packet.get_dummy(int(
                self.block_count[queue_index])*self.counter+run_index, self.data_len[queue_index],head_size=self.head_size))
        elif self.dummy_mode == "prev":
            self.outqueues[queue_index].put(Packet.get_dummy(int(
                self.block_count[queue_index])*self.counter+run_index, p_data=self.prev_data[queue_index],head_size=self.head_size))
        else:
            raise ValueError(
                f"\"{self.dummy_mode}\" is no possible mode for dummy-packet. Only \"zero\" or \"prev\".")

    def head_join(self, packet_head):
        """combines the heads and checks if finish-flag is set

        Arguments:
            packet_head {int} -- one head, which will be combined with the others of one run
        """
        if not self.connection_queue and (packet_head & 1 << 5):
            self.finish_event.set()
        self.outputhead = self.outputhead | packet_head

    def __str__(self):
        if self.connection_queue:
            return "SQN_Checker (middle)"
        else:
            return "SQN_Checker (sink)"

    def __repr__(self):
        return str(self)


class SendBlock(threading.Thread):
    def __init__(self, root, job, outqueues, connection_queue, command_rst, finish_event=None, head_size=1, sqn_size=8, **kwargs):
        """ - Compute sequence numbers for source jobs
            - Checks the flags in Head
            - Reset of sequence numbers, if the there is a command

        Arguments:
            root {str} -- root path for pipes
            job {Job} -- job , which is running on the current node
            outqueues {queue} -- queue for output-pipes to put the output-blocks
            connection_queue {queue} -- queue, where SQN-Check put the sqn, in type of packet
            command_rst {queue} -- command to reset
            finish_event {threading.Event} -- if the finish flag is set, then the job should be ended, by using this finish_event

        Keyword Arguments:
            head_size {int} -- Size of the head (default: {1})
            sqn_size {int} -- Size of the sequence number (default: {8})
        """
        super().__init__(**kwargs)
        self.root = root
        self.job = job
        self.outqueues = outqueues
        self.command_rst = command_rst
        self.connection_queue = connection_queue
        self.source_sqn = 0
        self.head_size = head_size
        self.sqn_size = sqn_size
        self.fds = []
        self.finish_event = finish_event
        self.finish_flag = False
        self._kill = False

    def read_pipe(self, file_obj, pipe):
        try:
            data_output = pipe.read_wrapper(file_obj)
            # logger.debug(f"READ from {pipe}: {data_output}")
            if not data_output:
                self.kill()
                return None
        except EOFError:
            self.kill()
            return None

        return data_output

    def read_out_job(self, file_obj, pipe, queue, reset, packet=None):
        """Read data from file_obj form the current job.

        Arguments:
            file_obj {file} -- File object  to read from
            pipe {Pipe} -- read from output-pipe of job
            queue {queue} -- outputqueue of job
            reset {bool} -- if true, set reset flag

        Keyword Arguments:
            packet {Packet} -- packet from the connection_queue(default: {None})
        """

        # Check if its a source job
        if len(self.job.inputs) == 0:
            if self.job.HEAD:
                head_job = int.from_bytes(file_obj.read(
                    self.head_size), byteorder="big")

                data_output = self.read_pipe(file_obj, pipe)
                if data_output == None:
                    self.kill()
                    return
                # Check if reset is True, then set reset-flag in head
                pkt = Packet((self.source_sqn).to_bytes(
                    self.sqn_size, byteorder='big') + head_job.to_bytes(
                    self.head_size, byteorder='big') + data_output)

                pkt.rst = bool(reset)
                # logger.debug(
                #     f"SENDBLOCK [{self.job}]: {pkt}......................................")
                queue.put(pkt)

            else:
                data_output = self.read_pipe(file_obj, pipe)
                if data_output == b'':
                    self.kill()

                # Check if  reset is True, then create 1 byte head, set reset-flag in head
                pkt = Packet((self.source_sqn).to_bytes(
                    self.sqn_size, byteorder='big') + (0).to_bytes(self.head_size, 'big') + data_output)

                pkt.rst = bool(reset)

                queue.put(pkt)

        else:
            if self.job.HEAD:
                # Read data and head from Job
                head_job = file_obj.read(packet.head_size)
                head_job = int.from_bytes(head_job, byteorder='big')

                data_output = self.read_pipe(file_obj, pipe)

                # Check corrupted-flag in head of job
                if head_job & (1 << (packet.head_size*8-1)):
                    pass
                else:
                    if packet.corrupted:
                        head_job = head_job ^ (1 << (packet.head_size*8-1))

                # Check reset-flag (normal jobs are not allowed to set it)
                if head_job & (1 << (packet.head_size*8-2)):
                    if packet.rst:
                        pass
                    else:
                        head_job = head_job ^ (1 << (packet.head_size*8-2))
                else:
                    if packet.rst:
                        head_job = head_job ^ (1 << (packet.head_size*8-2))

                # Check finish-flag in head of job
                if head_job & (1 << (packet.head_size*8-3)):
                    self.finish_flag = True
                else:
                    if packet.finished:
                        head_job = head_job ^ (1 << (packet.head_size*8-3))
                        self.finish_flag = True

                queue.put(Packet(struct.pack('!Q', packet.sqn) +
                                 head_job.to_bytes(self.head_size, 'big') + data_output))

            else:
                data_output = self.read_pipe(file_obj, pipe)
                queue.put(Packet(packet.full_data + data_output))

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def run(self):
        for pipe in self.job.outputs:
            path = f"{self.root}/fifo/{self.job.id}/{pipe.id}.fifo"
            # path = f"{self.root}/{pipe.id}.fifo"
            try:
                logger.debug(f"SendBlock: Opening {path}.")
                self.fds.append(open(path, "rb"))
            except Exception as e:
                logger.exception(
                    f"SendBlock: {e} occured while opening {path}.")
                raise e
        while True:
            if self._kill:
                for fd in self.fds:
                    try:
                        fd.close()
                    except:
                        pass
                break

            # Set the flag in self.finish_event
            if self.finish_flag:
                self.finish_event.set()
                self.finish_flag = False

            # Check if its source job
            if len(self.job.inputs) > 0:
                packet = self.connection_queue.get()
                reset_flag = None

            # Set reset-flag, if source_sqn == 0
            elif self.source_sqn == 0:
                packet = None
                reset_flag = True
                self.source_sqn += 1

            else:
                packet = None
                try:
                    reset_flag = self.command_rst.get(False)
                    # Check Reset as Timestamp
                    if isinstance(reset_flag, bool):
                        pass
                    else:
                        if reset_flag > time.time():
                            wait_sec = reset_flag - time.time()
                            time.sleep(wait_sec)
                            reset_flag = True
                    self.source_sqn = 0

                except queue.Empty:
                    reset_flag = None

                self.source_sqn += 1

            for fd, pipe, q in zip(self.fds, self.job.outputs, self.outqueues):
                self.read_out_job(fd, pipe, q, reset_flag, packet)

    def __str__(self):
        if self.connection_queue:
            return "SendBlock (middle)"
        else:
            return "SendBlock (source)"

    def __repr__(self):
        return str(self)


class SendSocket(threading.Thread):
    def __init__(self, ip, port, socketqueue, seq_size=8, head_size=1, **kwargs):
        """
        Send the outputblock from the socketqueue to the node with the ip
        The socket is defined by ip and the port

        Arguments:
            ip {str} -- ip of the node, where the outputblock needs to be send
            port {int} -- identify the specific job, which needs the outputblock
            socketqueue {queue} --  queue for the outputblocks
        Keyword Arguments:
            seq_size {int} -- size of the sequence number (default: {8})
            head_size {int} -- size of head (default: {1})
        """
        self.socketqueue = socketqueue
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(10)
        self.ip = ip
        self.port = port
        self.seq_size = seq_size
        self.head_size = head_size
        self._kill = False
        super().__init__(**kwargs)

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def run(self):
        while True:
            try:
                if self._kill:
                    self.socket.close()
                    break
                else:
                    logger.debug(
                        f"SendSocket: Connecting with {self.ip}:{self.port}.")
                    self.socket.connect((self.ip, self.port))
                    logger.debug(
                        f"SendSocket: Connection with {self.ip}:{self.port} established.")
                    break
            except socket.error:
                time.sleep(.5)

        fd = self.socket.makefile("wb", buffering=0)
        writer = pickle.Pickler(fd, protocol=pickle.HIGHEST_PROTOCOL)

        while True:
            if self._kill:
                self.socket.close()
                break
            send_object = self.socketqueue.get()
            # logger.debug(
            #     f"SendSocket: Sending {send_object} to {self.ip}:{self.port}")
            writer.dump(send_object)

    def redirected_copy(self, ip):
        obj = type(self)(ip, self.port, self.socketqueue,
                         self.seq_size, self.head_size, daemon=True)
        return obj

    def __str__(self):
        return f"SendSocket->({self.ip}:{self.port})"

    def __repr__(self):
        return str(self)


class InputServer(threading.Thread):
    """
    Waiting and accepting new tcp-connections
    """

    def __init__(self, pipe, queue, seq_size=8, head_size=1, port_offset=2000, **kwargs):
        self.pipe = pipe
        self.queue = queue
        self.seq_size = seq_size
        self.head_size = head_size
        self.handler = None
        self._kill = False
        # NOTE maybe implement different socket types (TCP/UDP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(10)
        self.port = pipe.id + port_offset
        self.socket.bind((pipe.destination, self.port))
        self.socket.listen(2)
        super().__init__(**kwargs)
        logger.debug(f"Created InputServer on port: {self.port}")

    def run(self):
        global logger
        while True:
            try:
                if self._kill:
                    self.socket.close()
                    break

                conn = self.socket.accept()

                if self.handler:
                    logger.warning(
                        "Dropping old connection as new connection arrived.")
                    self.handler.kill()

                logger.debug(f"Connected with {conn[1]}")
                self.handler = InputHandler(
                    conn[0], self.queue, self.pipe, daemon=True)
                # self.handler.socket.settimeout(10)
                self.handler.start()

            except socket.timeout:
                pass

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def __str__(self):
        return f"InputServer->({self.port})"

    def __repr__(self):
        return str(self)


class InputHandler(threading.Thread):
    def __init__(self, socket, queue, pipe, **kwargs):
        self.socket = socket
        self.queue = queue
        self.pipe = pipe
        self._kill = False
        super().__init__(**kwargs)

    def run(self):
        global logger
        logger.debug(f"InputHandler: Handler started.")

        file = self.socket.makefile("rb")
        loader = pickle.Unpickler(file)
        while True:
            try:
                if self._kill:
                    self.socket.close()
                    file.close()
                    break

                pkt = loader.load()
                # logger.debug(
                #     f"InputHandler({self.socket.getsockname()[1]}): Received {pkt}.")
                if self.pipe.ASYNC:
                    try:
                        self.queue.put_nowait(pkt)
                    except queue.Full:
                        try:
                            self.queue.get_nowait()
                        except queue.Empty:
                            self.queue.put(pkt)
                else:
                    self.queue.put(pkt)

            except socket.timeout:
                logger.debug(
                    f"InputHandler({self.socket.getsockname()[1]}): Socket timed out, creating new file.")

            except (pickle.UnpicklingError, EOFError):
                logger.error(
                    f"InputHandler({self.socket.getsockname()[1]}): Fatal error, shutting down...")
                break
            except:
                logger.exception(
                    f"InputHandler({self.socket.getsockname()[1]}): Error while reading:")
                break

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True


class ReadPipe(threading.Thread):
    """
    Reading the pipe between wrappers
    """

    def __init__(self, path, pipe, queue, seq_size=8, head_size=1, **kwargs):
        self.queue = queue
        self.pipe = pipe
        self.seq_size = seq_size
        self.head_size = head_size
        self.path = path
        self._kill = False
        super().__init__(**kwargs)

    def run(self):
        logger.debug(f"Opening ReadPipe on {self.path}")
        try:
            if not os.path.exists(self.path):
                logger.debug(
                    f"ReadPipe: {self.path} did not exist, creating it...")
                os.mkfifo(self.path)
        except Exception as e:
            logger.warning(
                f"ReadPipe: {self.path} did not exist, error while trying to create it: {e}")

        fd = open(self.path, "rb")
        loader = pickle.Unpickler(fd)
        while True:
            if self._kill:
                fd.close()
                break
            try:
                pkt = loader.load()
                # logger.debug(f"{self.pipe}: Read {pkt}")
                if self.pipe.ASYNC:
                    try:
                        self.queue.put_nowait(pkt)
                    except queue.Full:
                        try:
                            self.queue.get_nowait()
                        except queue.Empty:
                            self.queue.put(pkt)
                else:
                    self.queue.put(pkt)

            except BrokenPipeError:
                logger.debug("ReadPipe: BROKEN PIPE")
            except pickle.UnpicklingError:
                logger.error(
                    f"ReadPipe: Error while reading {self.pipe}, shutting down...")
                exit(1)
            except EOFError:
                continue

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def __str__(self):
        return f"ReadPipe->({self.path})"

    def __repr__(self):
        return str(self)


class WritePipe(threading.Thread):
    """
    Writing in the pipe between wrappers
    """

    def __init__(self, path, pipe, queue, head, wrapper_pipe=False, seq_size=8, head_size=1, **kwargs):
        self.queue = queue
        self.pipe = pipe
        self.seq_size = seq_size
        self.head = head
        self.wrapper_pipe = wrapper_pipe
        self.head_size = head_size
        self.path = path
        self._kill = False
        super().__init__(**kwargs)

    def run(self):
        import os
        global logger
        logger.debug(
            f"Opening WritePipe {self.path}, wrapper_pipe = {self.wrapper_pipe}")
        try:
            if not os.path.exists(self.path):
                logger.debug(
                    f"WritePipe: {self.path} did not exist, creating it...")
                os.mkfifo(self.path)
        except Exception as e:
            logger.warning(
                f"WritePipe: {self.path} did not exist, error while trying to create it: {e}")

        fd = open(self.path, "wb", 0)
        writer = pickle.Pickler(fd, protocol=pickle.HIGHEST_PROTOCOL)
        while True:
            if self._kill:
                fd.close()
                break
            try:
                data = self.queue.get()

                if self.wrapper_pipe:
                    # logger.debug(f"WritePipe (outter) writing: {data}")
                    writer.dump(data)
                else:
                    # logger.debug(f"Writing for inner pipe: {data}")
                    if self.pipe.ASYNC:
                        data.rst = False
                    data = data.full_data[self.seq_size:] if self.head else data.data
                    fd.write(data)

            except BrokenPipeError:
                logger.debug("WritePipe: Pipe was closed, shutting down.")
                exit(1)

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def __str__(self):
        return f"WritePipe->({self.path})"

    def __repr__(self):
        return str(self)


class CommandServer(threading.Thread):
    def __init__(self, ip, port, reset_queue, redirect_queue, **kwargs):
        self.reset_queue = reset_queue
        self.redirect_queue = redirect_queue
        self._kill = False
        self.port = port
        # NOTE maybe implement different socket types (TCP/UDP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(10)
        logger.debug(f"Starting CommandServer on port: {port}")
        self.socket.bind((ip, self.port))
        self.socket.listen(5)
        super().__init__(**kwargs)

    def run(self):
        while True:
            try:
                if self._kill:
                    self.socket.close()
                    break

                conn = self.socket.accept()

                logger.debug(f"CommandServer: Connected with {conn[1]}")
                self.handler = CommandHandler(
                    *conn, reset_queue=self.reset_queue, redirect_queue=self.redirect_queue, daemon=True)
                self.handler.socket.settimeout(1)
                self.handler.start()

            except socket.timeout:
                pass

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def __str__(self):
        return f"CommandServer->({self.port})"

    def __repr__(self):
        return str(self)


class CommandHandler(threading.Thread):
    def __init__(self, socket, conn, reset_queue, redirect_queue, **kwargs):
        self.socket = socket
        self.conn = conn
        self.socket.settimeout(1)
        self.reset_queue = reset_queue
        self.redirect_queue = redirect_queue

        logger.debug(f"Created CommandHandler for {conn}")
        super().__init__(**kwargs)

    def run(self):
        try:
            message = str(self.socket.recv(4096), 'utf-8')
        except socket.error:
            logger.warning(f"Timeoute while reading command from {self.conn}")
        except Exception as e:
            logger.exception(f"Exception occured while reading command: {e}")
        try:
            command = json.loads(message)
        except json.JSONDecodeError:
            logger.exception(f"JSON decode error while decoding: {message}")

        self.socket.close()

        logger.debug(f"CommandHandler: Received Command: {command}")

        if 'REDIRECT' in command:
            self.redirect_queue.put(command['REDIRECT'])
        if 'RESET' in command:
            self.reset_queue.put(command['RESET'])


class RedirectHandler(threading.Thread):
    def __init__(self, job, my_ip, redirect_queue, in_pipes, out_pipes, wrapper_in, wrapper_out, root,
                 port_offset=2000, **kwargs):
        self.job = job
        self.redirect_queue = redirect_queue
        self.my_ip = my_ip
        self.in_pipes = in_pipes
        self.out_pipes = out_pipes
        self.wrapper_in = wrapper_in
        self.wrapper_out = wrapper_out
        self.root = root
        self.port_offset = port_offset
        self._kill = False
        super().__init__(**kwargs)

    def get_index_in_pipes(self, pipe_id):
        for index, p in enumerate(self.in_pipes):
            if p.id == pipe_id:
                return index
        return None

    def get_index_out_pipes(self, pipe_id):
        for index, p in enumerate(self.out_pipes):
            if p.id == pipe_id:
                return index
        return None

    def run(self):

        while True:
            if self._kill:
                break
            try:
                command = self.redirect_queue.get()
                logger.debug(f"RedirectHandler: CMD: {command}")
                for pipe_id, ip in command.items():
                    pipe_id = int(pipe_id)
                    index_in = self.get_index_in_pipes(pipe_id)
                    index_out = self.get_index_out_pipes(pipe_id)
                    # redirect to same node
                    if ip == self.my_ip:
                        # handle redirect incoming connection
                        if index_in is not None:
                            thread = self.wrapper_in[index_in]
                            if isinstance(thread, ReadPipe):
                                continue
                            elif isinstance(thread, InputServer):
                                if thread.handler:
                                    thread.handler.kill()
                                thread.kill()
                                path = f'{self.root}/fifo/{pipe_id}.fifo'
                                pipe = thread.pipe
                                queue = thread.queue
                                thread = ReadPipe(path, pipe, queue,
                                                  seq_size=thread.seq_size,
                                                  head_size=thread.head_size,
                                                  daemon=True)
                                thread.start()
                                self.wrapper_in[index_in] = thread

                        # handle rredirect outgoing connectio
                        if index_out is not None:
                            thread = self.wrapper_out[index_out]
                            if isinstance(thread, WritePipe):
                                continue
                            elif isinstance(thread, SendSocket):
                                thread.kill()
                                path = f'{self.root}/fifo/{pipe_id}.fifo'
                                pipe = self.out_pipes[index_out]
                                queue = thread.socketqueue
                                thread = WritePipe(path, pipe, queue,
                                                   head=False,
                                                   wrapper_pipe=True,
                                                   seq_size=thread.seq_size,
                                                   head_size=thread.head_size,
                                                   daemon=True)
                                thread.start()
                                self.wrapper_out[index_out] = thread

                    else:
                        if index_in is not None:
                            thread = self.wrapper_in[index_in]
                            if isinstance(thread, InputServer):
                                continue
                            elif isinstance(thread, ReadPipe):
                                thread.kill()
                                pipe = thread.pipe
                                queue = thread.queue
                                thread = InputServer(pipe, queue,
                                                     seq_size=thread.seq_size,
                                                     head_size=thread.head_size,
                                                     port_offset=self.port_offset,
                                                     daemon=True)
                                thread.start()
                                self.wrapper_in[index_in] = thread

                        if index_out is not None:
                            thread = self.wrapper_out[index_out]
                            if isinstance(thread, WritePipe):
                                thread.kill()
                                port = self.port_offset + self.job.id
                                queue = thread.queue
                                thread = SendSocket(ip, port, queue,
                                                    daemon=True)
                                thread.start()
                                self.wrapper_out[index_out] = thread

                            elif isinstance(thread, SendSocket):
                                if thread.ip == ip:
                                    continue
                                thread.kill()
                                thread = thread.redirected_copy(ip)
                                thread.start()
                                self.wrapper_out[index_out] = thread
            except Exception as e:
                logger.exception(
                    f"RedirectHandler: Error while processing: {e}")

    def kill(self):
        logger.debug(f"Killing {self}...")
        self._kill = True

    def __str__(self):
        return f"RedirectHandler"

    def __repr__(self):
        return str(self)
