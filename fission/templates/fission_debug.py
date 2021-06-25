#!/usr/bin/env python3
import argparse
import pprint
import os
import select
import socket
import sys
import json
import queue
import threading
import time

class JobInfo():
    def __init__(self, name, ip, port, shift=0):
        self.name = name
        self.ip = ip
        self.port = port
        self.socket = None
        self.shift = shift

    def connect(self):
        print(f"Connecting to ({self.ip}, {self.port})")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for _ in range(50):
            try:
                self.socket.connect((self.ip, self.port))
                break
            except socket.error:
                time.sleep(.1)

        self.socket.settimeout(1)
        self.fd = self.socket.makefile('r')

    def update(self, d):
        if self.ip != d['ip']:
            self.ip = d['ip']
            self.socket.close()
            self.connect()

    def print(self):
        try:
            line = self.fd.readline()
            if line:
                print("{:>{shift}} ({}) -> {}".format(self.name, self.ip, line, shift=self.shift), end="")
        except socket.error:
            pass


def read_pipe(fd, q):
    #sys.stderr = open("debugger_err.txt", "w")
    while True:
        try:
            data = fd.readline()
            if not data:
                time.sleep(.5)
                continue
            jobs = json.loads(data)
            print(f"Network Information:")
            pprint.pprint(jobs)
            q.put(jobs)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    in_queue = queue.Queue()

    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--ip", action="append", required=False)
    parser.add_argument("--port", action="append", required=False)
    parser.add_argument("--pipe", "-p", required=False)
    args = parser.parse_args()

    if args.pipe:
        fd = open(args.pipe.strip(), "r")

        thread = threading.Thread(target=read_pipe, args=(fd, in_queue), daemon=True)
        thread.start()
        print("Thread Start")

        jobs = in_queue.get()
        try:
            shift = max([len(j['name']) for j in jobs])
            jobs = [JobInfo(**job, shift=shift) for job in jobs]
        except:
            input("Invalid Jobs received, enter to quit...")
            exit(1)


    elif args.ip and args.port:
        jobs = [JobInfo("", ip, int(port)) for ip, port in zip(args.ip, args.port)]
    else:
        raise RuntimeError("Invalid Arguments")
    
    for job in jobs:
        job.connect()

    try:
        while True:
            new_jobs = []
            if args.pipe:
                try:
                    # read all if many
                    while True:
                        new_jobs = in_queue.get_nowait()
                except queue.Empty:
                    pass

                for info, new in zip(jobs, new_jobs):
                    info.update(new)

            readySockets = select.select(
                [job.socket for job in jobs], [], [], 1)[0]

            for s in readySockets:
                for j in jobs:
                    if j.socket is s:
                        j.print()
    except KeyboardInterrupt:
        for job in jobs:
            try:
                job.socket.terminate()
                job.socket.close()
            except Exception:
                pass
    
    input("Press enter to exit...")
