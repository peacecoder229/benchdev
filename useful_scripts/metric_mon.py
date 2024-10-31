import os
import logging
import time
from basic_monitor import BasicMonitor

# may use perf
# This monitor only valid on 1/2 socket system after SKX gen.
class metricMonitor(BasicMonitor):
    def __init__(self, name="basic_monitor"):
        self.name = name
        self.output = {}

    def start_recording(self, core, log_path="./"):
        #cmd_mpki_hp = "perf stat -o %shp_mpki.log -C %s -I 1000 -e instructions,cache-misses,mem-loads,mem-stores &"%(log_path, hp_core)
        #cmd_mpki_lp = "perf stat -o %slp_mpki.log -C %s -I 1000 -e instructions,cache-misses,mem-loads,mem-stores &"%(log_path, lp_core)
        cmd_metric = "perf stat -o %smetric.log -C %s -I 2000 -e tsc,r003c,r00c0,cycle_activity.stalls_mem_any --interval-count=150 &"%(log_path, core)
        try:
            print cmd_metric
            os.system(cmd_metric)
        except:
            self.output["status"] = 0
        return True
 
    def return_metrics(self):
        try:
            #output0 = os.popen(r'ls')
            self.output = {}
            output1 = os.popen('tail -n4 metric.log | awk \'{print $2}\'')
            tsc = float(output1.readline().replace(',', ''))
            cycle = float(output1.readline().replace(',', ''))
            instruction = float(output1.readline().replace(',', ''))
            memstalls = float(output1.readline().replace(',', ''))
            self.output["util"] = cycle/tsc
            self.output["ipc"] = instruction/cycle
            self.output["stallratio"] =  memstalls/cycle
        except:
            self.output["status"] = 0
        return self.output 

if __name__ == "__main__":
    IMC_M = metricMonitor()
    IMC_M.start_recording("0-13,14-27")
    while 1:
        metrics_output = IMC_M.return_metrics()
        print metrics_output
        time.sleep(1)
        
