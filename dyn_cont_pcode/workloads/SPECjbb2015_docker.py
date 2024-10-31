#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from workload import Workload


class SPECjbb2015(Workload):
    def __init__(self, PID, cores, COS, resource_list):
        name = 'specjbb2015'
        super(SPECjbb2015, self).__init__(name, PID, cores, COS, resource_list)

    def start_workload(self, ir_config=4000, duration_config=170000):
        ir = ir_config
        duration = duration_config
        cores = self.cores
        name = self.name
        output_path = "./"
        opt = "-server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15 -XX:ParallelGCThreads=28 -Xloggc:./gc.log -XX:+PrintGCDateStamps -XX:MaxPermSize -Xmx40g -Xms40g -Xmn40g"
        cmd = "docker run --name HP-%s-IR%s --rm -v `pwd`/%s:/result -e CONF_IR=%s -e CONF_DURATION=%s " \
              "-e PRESETSTEP=2000 -e ADDTXTOUT=2000 -e JAVA_OPTS=\"%s\" --cpuset-cpus=%s specjbb2015:quick &" % (name, ir, output_path, ir, duration, opt, cores)
        os.system(cmd)

    def stop_workload(self):
        cmd = "docker ps -a | grep %s | awk '{print $1}' | xargs docker rm -f" % self.name
        os.system(cmd)

if __name__ == "__main__":
    D = SPECjbb2015('1','0-8','4',[123,456])
    D.start_workload()
