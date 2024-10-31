#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from workload import Workload


class Stream(Workload):
    def __init__(self, PID, cores, COS, resource_list):
        name = 'stream'
        super(Stream, self).__init__(name, PID, cores, COS, resource_list)

    def start_workload(self):
        docker_name=str(self.name)+str(self.PID)
        cmd = "docker run --cpuset-cpus=%s -d --name %s stream" % (self.cores, docker_name)
        os.popen(cmd)

    def stop_workload(self):
        docker_name = str(self.name) + str(self.PID)
        cmd = "docker ps -a | grep %s | awk '{print $1}' | xargs docker rm -f" % docker_name
        os.system(cmd)


if __name__ == "__main__":
    D = Workload('Specjbb2015', '0-55')
