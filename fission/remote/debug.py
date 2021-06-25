import threading
import logging
import socket
import os

logger = logging.getLogger(__name__)


class MultiWrite(threading.Thread):
    def __init__(self, *args, **kwargs):
        """This is a thread object and file like.
        You can attach handler which will be written to with 'attach'.
        If you need a actual file object use the property `writer` to
        retrieve a text writer and 'start' to start the underlying thread.
        """
        self.handlers = list(args)
        self._kill = False
        r, w = os.pipe()
        self._reader = open(r, "r")
        self._writer = open(w, "w")

        super().__init__(**kwargs)

    def close(self):
        self._reader.close()
        self._writer.close()

    def getvalue(self):
        return b''
        # return self.handlers[0].get_value()

    def attach(self, handler):
        logger.debug(f"Attaching {handler} to MultiWrite. [{self.handlers}]")
        self.handlers.append(handler)

    # def attach_subprocess(self, proc):
    #     self.proc_stdout = proc.stdout
    #     self.start()

    def write(self, data):
        errors = []
        for i, f in enumerate(self.handlers):
            try:
                f.write(data)
                f.flush()
            except (BlockingIOError, BrokenPipeError, ConnectionResetError):
                errors.append(i)
            except Exception:
                logger.exception("Error while writing...")

        for e in errors[::-1]:
            removed = self.handlers.pop(e)
            logger.warning(
                f"MultiWrite: Removed {removed} due to BlockingIOError.")

    @property
    def writer(self):
        return self._writer

    def run(self):
        logger.debug("Starting MultiWrite")
        while True:
            if self._kill:
                break
            try:
                # logger.debug(f"MultiWrite: Reading from {self.proc_stdout}")
                # data = self.proc_stdout.readline()
                # logger.debug(f"MultiWrite: Reading from {self._reader}")
                data = self._reader.readline()

                self.write(data)

            except Exception as e:
                logger.exception(f"{e}")

    def kill(self):
        self._kill = True


class DebugServer(threading.Thread):
    def __init__(self, ip, port, multi_write, **kwargs):
        """Attaches every incomming connection to the given MultiWrite object.

        Arguments:
            threading {[type]} -- [description]
            ip {str} -- IP to listen on
            port {int} -- port to listen on
            multi_write {MultiWrite} -- MultiWrite object to attach handlers to.
        """
        self._kill = False
        self.multi_write = multi_write

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(10)

        self.socket.bind((ip, port))
        self.socket.listen(5)
        super().__init__(**kwargs)

    def run(self):
        logger.debug(f"Starting DebugServer.")
        while True:
            try:
                if self._kill:
                    self.socket.close()
                    break

                conn = self.socket.accept()

                logger.info(f"Debugger attached from {conn[1]}")

                conn[0].setblocking(0)

                self.multi_write.attach(conn[0].makefile('w'))

            except socket.timeout:
                pass

    def kill(self):
        self._kill = True
