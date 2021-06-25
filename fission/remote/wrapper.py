def pipe_wrapper_sync(job, root, init=False, debug=False, port_offset=2000, ip_addr=None, log_level='DEBUG'):
    import sys
    import os
    import logging
    import queue
    import time
    import subprocess
    import signal
    import threading

    import fission.remote.synchronization as sync
    import fission.remote.debug as fission_debug
    from fission.core.jobs import LocalJob

    try:
        ip_addr = dispy_node_ip_addr
    except NameError:
        if not ip_addr:
            ip_addr = 'localhost'

    # Convert pipe destination and source in case
    # they were not pickled
    for p in job.inputs + job.outputs:
        if not isinstance(p.source, str):
            p._source = p.source.allocated.ip
        if not isinstance(p.destination, str):
            p._destination = p.destination.allocated.ip

    os.makedirs(root, exist_ok=True)

    logger = logging.getLogger("fission")

    #c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(f'{root}/fission.log')
    # c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.getLevelName(log_level))

    # Create formatters and add it to handlers
    #c_format = logging.Formatter('%(levelname)s:  %(message)s')
    f_format = logging.Formatter(
        f'%(asctime)s - %(name)s - %(levelname)s [JOB:{job.id}] - %(message)s')
    # c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    # logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    logger.setLevel(logging.DEBUG)

    logger.debug(f"Starting {job} with debug={debug}")

    if debug:
        _stdout = sys.stdout
        _stderr = sys.stderr
        debug_port = port_offset - (2*job.id)
        #logger.debug("Starting DebugServer")
        redirect_output = fission_debug.MultiWrite(sys.stdout, daemon=True)
        redirect_output.start()

        debug_thread = fission_debug.DebugServer(
            ip_addr, debug_port, redirect_output, daemon=True)
        debug_thread.start()

    else:
        redirect_output = False

    try:
        logger.debug(f"Creating: {root}/{job.id}")
        os.makedirs(f"{root}/{job.id}", exist_ok=True)
        logger.debug(f"Creating: {root}/fifo/{job.id}/")
        os.makedirs(f"{root}/fifo/{job.id}/", exist_ok=True)
        assert os.path.isdir(f"{root}/{job.id}")
        #logger.debug(f"Checking exists: {path}/{job.id}/{job.executable}")
        #assert os.path.exists(f"{path}/{job.id}/{job.executable}")
    except AssertionError:
        logger.exception("Sanity check failed, shutting down.")
        exit(1)

    try:

        # ─── CREATING PIPES ─────────────────────────────────────────────────────────────
        finish_event = threading.Event()

        connecting_queue = queue.Queue(job.MAX_QUEUE)
        reset_queue = queue.Queue()
        redirect_queue = queue.Queue()
        inQueues = []
        inQueues2 = []
        outQueues = []
        inFiles = []
        outFiles = []

        ALL_ASYNC = all(map(lambda x: x.ASYNC, job.inputs))

        logger.debug(f"Creating ingoing {len(job.inputs)} Pipes.")
        # get ingoing
        for ingoing in job.inputs:
            if ingoing.ASYNC:
                # use same queue for read and write
                # this completely bypasses SQN_Checker
                q = queue.Queue(job.MAX_QUEUE)
                inQueues.append(q)
                inQueues2.append(q)
            else:
                inQueues.append(queue.Queue())
                inQueues2.append(queue.Queue())

            pipes = [f"{root}/fifo/{job.id}/{ingoing.id}.fifo"]
            if ingoing.source == ip_addr:
                pipes.append(f"{root}/fifo/{ingoing.id}.fifo")

            for pipe in pipes:
                if os.path.exists(pipe) and init:
                    os.remove(pipe)
                    os.mkfifo(pipe)
                elif not os.path.exists(pipe):
                    # raise condition may cause pipe creating
                    # while pipe already exists
                    try:
                        os.mkfifo(pipe)
                    except FileExistsError:
                        pass

                logger.debug(f"Created pipe {pipe} (ingoing).")

            pipes = tuple(pipes) if len(pipes) == 2 else tuple(pipes + [None])

            inFiles.append(pipes)

        # all threads that won't be changed while job is running
        static_threads = []

        # threads which handle wrapper input
        wrapper_in_threads = []

        for (inpipe, local), pipe, queue1, queue2 in zip(inFiles, job.inputs, inQueues, inQueues2):
            # TODO make seq and head size variable
            if local:
                wrapper_in_threads.append(sync.ReadPipe(
                    local, pipe, queue1, daemon=True))
                static_threads.append(sync.WritePipe(
                    inpipe, pipe, queue2, job.HEAD, daemon=True))
            else:
                wrapper_in_threads.append(
                    sync.InputServer(pipe, queue1, daemon=True))
                static_threads.append(sync.WritePipe(
                    inpipe, pipe, queue2, job.HEAD, daemon=True))

        if job.outputs and job.inputs and not ALL_ASYNC:
            static_threads.append(sync.SQN_Checker(
                inQueues, inQueues2, job.inputs, connecting_queue, finish_event=finish_event, daemon=True))
        elif job.inputs and not ALL_ASYNC:
            static_threads.append(sync.SQN_Checker(
                inQueues, inQueues2, job.inputs, None, finish_event=finish_event, daemon=True))

        logger.debug(f"Creating outgoing {len(job.outputs)} Pipes")
        # get outgoing
        for outgoing in job.outputs:
            outQueues.append(queue.Queue())

            pipes = [f"{root}/fifo/{job.id}/{outgoing.id}.fifo"]
            if outgoing.destination == ip_addr:
                pipes.append(f"{root}/fifo/{outgoing.id}.fifo")

            for pipe in pipes:
                if os.path.exists(pipe) and init:
                    os.remove(pipe)
                    os.mkfifo(pipe)
                elif not os.path.exists(pipe):
                    # raise condition may cause pipe creating
                    # while pipe already exists
                    try:
                        os.mkfifo(pipe)
                    except FileExistsError:
                        pass

                logger.debug(f"Created pipe {pipe} (outgoing).")

            pipes = tuple(pipes) if len(pipes) == 2 else tuple(pipes + [None])

            outFiles.append(pipes)

        wrapper_out_threads = []

        for (inpipe, local), pipe, queue1 in zip(outFiles, job.outputs, outQueues):
            # TODO make seq and head size variable
            if local:
                logger.debug(
                    f"Starting WritePipe with {local}, {pipe}, {queue1}, {job.HEAD}, wrapper_pipe=True")
                wrapper_out_threads.append(sync.WritePipe(
                    local, pipe, queue1, job.HEAD, wrapper_pipe=True, daemon=True))
            else:
                logger.debug(
                    f"Starting SendSocket for {pipe.destination}:{pipe.id + port_offset}.")
                wrapper_out_threads.append(sync.SendSocket(
                    pipe.destination, pipe.id + port_offset, queue1, daemon=True))

        # _head_size for each pipe is expected to be the same
        if job.outputs and job.inputs and not ALL_ASYNC:
            static_threads.append(sync.SendBlock(
                root, job, outQueues, connecting_queue, reset_queue, head_size=job.outputs[0]._head_size, daemon=True))
        elif job.outputs or ALL_ASYNC:
            static_threads.append(sync.SendBlock(
                root, job, outQueues, None, reset_queue, finish_event, head_size=job.outputs[0]._head_size, daemon=True))

        command_port = port_offset - (job.id*2 - 1)
        static_threads.append(sync.CommandServer(
            ip_addr, command_port, reset_queue, redirect_queue, daemon=True))

        static_threads.append(sync.RedirectHandler(job=job, my_ip=ip_addr, redirect_queue=redirect_queue,
                                                   in_pipes=job.inputs, out_pipes=job.outputs,
                                                   wrapper_in=wrapper_in_threads, wrapper_out=wrapper_out_threads,
                                                   root=root, port_offset=port_offset, daemon=True))

        all_threads = wrapper_in_threads + static_threads + wrapper_out_threads

        logger.info(
            f"@{job} starting {len(all_threads)} threads: static {static_threads} "
            f"| in {wrapper_in_threads} | out {wrapper_out_threads}")

        for thread in all_threads:
            logger.debug(f"Starting thread {thread}...")
            thread.start()

        #
        # ─────────────────────────────────────────────────────────────────────────  ─────
        #

        # ─── SIGNAL HANDLING ────────────────────────────────────────────────────────────

        def sig_term(signalNumber, frame):
            # TODO handle sig term
            logger.debug("SIGTERM received. Shutting down subprocess.")
            if proc:
                proc.kill()

            for thread in all_threads:
                try:
                    thread.kill()
                except:
                    pass

            sys.exit(0)


        signal.signal(signal.SIGTERM, sig_term)

        #
        # ─────────────────────────────────────────────────────────────────────────  ─────
        #

        # ─── STARTING SUBPROCESS ────────────────────────────────────────────────────────

        logger.debug("Executing {}.".format(job))

        proc = None

        if job.CREATES_SUBPROCESS or job.is_source():
            proc = job.start(root=root, seperate_job_pipes=True,
                             redirect_stdout_stderr=redirect_output)

            if not job.CREATES_SUBPROCESS:
                finish_event.set()

        else:
            arguments = {"root": root, "seperate_job_pipes": True,
                         "redirect_stdout_stderr": redirect_output}
            job_thread = threading.Thread(
                target=job.start, kwargs=arguments, daemon=True)
            job_thread.start()

        # proc is returned if subprocess is spawned
        if job.CREATES_SUBPROCESS and job.is_source():
            if not redirect_output:
                std_out, std_err = proc.communicate()

                if std_err:
                    logger.info(f"{job} failed with stderr:\n{std_err}:")

                if std_out:
                    logger.info(f"{job} finished with stdout:\n{std_out}")

                return_string = "{}".format(std_out) if std_out else ""

                return return_string
            else:
                exit_code = proc.wait()
                logger.info(f"{job} finished with code: {exit_code}:")
        else:
            logger.debug(f"{job} waiting for finish event...")
            finish_event.wait()

        if outQueues:
            while not all(map(lambda x: x.empty(), outQueues)):
                time.sleep(.25)
            # sleep a bit
            time.sleep(.5)

        if job.CREATES_SUBPROCESS and not job.is_source() and not redirect_output:
            try:
                proc.terminate()
                std_out, std_err = proc.communicate(timeout=1)

                if std_err:
                    logger.info(f"{job} failed with stderr:\n{std_err}:")

                if std_out:
                    logger.info(f"{job} finished with stdout:\n{std_out}")

                return_string = "{}".format(std_out) if std_out else ""

                return return_string

            except subprocess.TimeoutExpired:
                logger.info(
                    f"{job} timed out while trying the retrieve outputs.")
                return_string = "Timeout while communicating"
                proc.kill()

        try:
            return return_string
        except NameError:
            pass

    except Exception as e:
        logger.exception("Error occured, shutting down.")
        raise e
