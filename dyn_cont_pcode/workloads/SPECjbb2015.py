#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from workload import Workload
from closelooplogger import ControllerLogger as CL


class SPECjbb2015(Workload):
    def __init__(self, PID, cores, COS, resource_list):
        name = 'specjbb2015'
        super(SPECjbb2015, self).__init__(name, PID, cores, COS, resource_list)
        self.last_hp_time=-1

    def start_workload(self, ir_config=4000, duration_config=170000):
        ir = ir_config
        duration = duration_config
        cores = self.cores
        name = self.name
        output_path = "./"
        opt = "-server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15 -XX:ParallelGCThreads=28 -Xloggc:./gc.log -XX:+PrintGCDateStamps -XX:MaxPermSize -Xmx40g -Xms40g -Xmn40g"
        cmd = "docker run --name HP-%s-IR%s --rm -v `pwd`/%s:/result -e CONF_IR=%s -e CONF_DURATION=%s " \
              "-e PRESETSTEP=2000 -e ADDTXTOUT=2000 -e JAVA_OPTS=\"%s\" --cpuset-cpus=%s specjbb2015:quick &" % (name, ir, output_path, ir, duration, opt, cores)
        

        with open('./specjbb2015/config.sh',"w") as f:
            f.write('export PRESETSTEP=2000\n')
            f.write('export ADDTXTOUT=2000\n')
            f.write('ir_config=%s\n'%ir)
            f.write('test_cores=%s\n'%cores)
        os.system('./specjbb2015/run_multi_var.sh &')

    def stop_workload(self):
        #cmd = "docker ps -a | grep %s | awk '{print $1}' | xargs docker rm -f" % self.name
        cmd = "pkill -9 java"
        os.system(cmd)

    def return_performance(self, input_file):
        try:
            output = os.popen('tail -20 %s|grep \'TotalPurchase\'' % input_file)
            result = output.read().split(',')[8]
            return float(result)
        except:
            return -1

    def return_time(self, input_file):
        try:
            output = os.popen('tail -20 %s|grep \'Performance\'' % input_file)
            result = output.read().split('s:')[0]
            return float(result)
        except:
            return -1

    def return_gc(self, input_file):
        try:
            output = os.popen('tail -1 %s |awk \'{print $2}\'' % input_file)
            result = output.read().split(':')[0]
            return float(result)
        except:
            return -1

    def SLA_function(self, latnecy_target=4000):
        performance = self.return_performance('./workloads/specjbb2015/*/controller.out')
        hp_time = self.return_time('./workloads/specjbb2015/*/controller.out')
        gc_time = self.return_gc('./workloads/specjbb2015/*/gc.log')
        CL().logger.info("Latest Application performance time: %s" % hp_time)
        CL().logger.info("Latest GC time: %s" % gc_time)
        if performance == -1 or hp_time == self.last_hp_time:
            CL().logger.warning("Cannot get performance data! Will retry later.")
            return -1
        self.last_hp_time=hp_time
        if performance > latnecy_target*100:
            CL().logger.warning("Abnormal latency result detected! May caused by GC.")
            return -1
        elif performance > latnecy_target:
            CL().logger.info("Latency issues detected, actual_latency: %s, target_latency: %s"%(performance, latnecy_target))
            return 1
        CL().logger.info("Normal latency result, actual_latency: %s, target_latency: %s" % (performance, latnecy_target))
        return 0

if __name__ == "__main__":
    D = SPECjbb2015('1','0-8','4',[123,456])
    D.start_workload()
