# -*- coding: utf-8 -*-
import os
import time
import urllib


class WorkloadClient():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def stop_workload(self, PID):
        f = urllib.urlopen("http://%s:%s/stop_workload?%s" % (self.ip, self.port, PID))
        return f.read()

    def apply_for_workload(self, cores):
        f = urllib.urlopen("http://%s:%s/apply_for_workload?%s" % (self.ip, self.port, cores))
        return f.read()

    def get_pending_workload(self):
        f = urllib.urlopen("http://%s:%s/get_pending_workload" % (self.ip, self.port))
        return f.read()

    def add_workload(self, type, priority="BE"):
        f = urllib.urlopen("http://%s:%s/add_workload?%s" % (self.ip, self.port, type))
        #print f.read()
        return f.read()


if __name__ == "__main__":
    C = WorkloadClient('127.0.0.1', 2035)
    #print C.add_workload("specjbb2015")
    #print C.add_workload("redis")
    print type(C.get_pending_workload())


