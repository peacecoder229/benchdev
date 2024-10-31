#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import wraps
import os
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import json
import logging
import logging.handlers  

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='monitor.log',
                    filemode='w')
file = logging.handlers.TimedRotatingFileHandler("log/monitor.log", "D")
#fmt = logging.Formatter("%(asctime)s - %(pathname)s - %(filename)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s")
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file.setFormatter(fmt)
file.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
CL = logging.getLogger('monitor')
CL.addHandler(console)
CL.addHandler(file)

def singleton(cls):
    instances = {}

    @wraps(cls)
    def getinstance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return getinstance

@singleton
class MonitorServerRedis():
    def __init__(self, qps=(14000, 15000), name='redis', result_path="/home/dianjuns/dynamic_resource_control/redis_output/"):
        self.name = name
        self.qps_target = qps
        self.result_path = result_path

    def get_cpu_utilization(self):
        # o = os.popen('mpstat | grep \'all\' | awk \'{print $4}\'')
        o = os.popen('top -n 2 -d 0.5 |grep Cpu | awk \'{print $2}\' |tail -1')
        util = o.read()
        return util.strip()

    def get_stream_instance(self):
        cmd = 'docker ps -a | grep stream | wc -l'
        o = os.popen(cmd)
        i = o.read()
        return int(i)

    def get_stream_finished(self):
        cmd = r"for i in `docker ps -a | grep stream | awk '{print $1}'`; do docker logs $i | tail -1; done"
        o = os.popen(cmd)
        counts = o.read()
        if counts == '':
            return 0
        l = counts.strip().split('\n')
        intl = [int(i) for i in l]
        c = sum(intl)
        return c

    def set_qps_target(self,target):
        self.qps_target=target
        CL.info("SLO target is set to:%s" % str(target))

    def return_performance(self, input_file):
        try:
            output = os.popen('tail -5 %s|grep requests | awk \'{print $1}\'' % input_file)
            result = output.read().strip()
            return float(result)
        except:
            return -1

    def SLA_function(self):
        performance = self.return_performance(self.result_path + 'redis*.log')
        util = self.get_cpu_utilization()
        stream_instance = self.get_stream_instance
        stream_count = self.get_stream_finished()
        CL.info("System CPU utilization: %s" % util)
        CL.info("Stream finished:%s" % stream_count)
        print performance
        if performance == -1:
            CL.warning("Cannot get performance data! Will retry in 5 sec.")
            return -1
        elif performance < self.qps_target[0]:
            CL.warning(
                "QPS issues detected, SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
            return 1
        elif performance > self.qps_target[1]:
            CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
            return 2
        CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
        return 0


#M = MonitorServer()
M = MonitorServerRedis()

class MonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # self.send_response(200)
            name = self.path.split('?')[0]
            if name == '/get_workload_performance':
                M = MonitorServerRedis()
                result = M.SLA_function()
            else:
                result = 'error'
        except:
            self.wfile.write(json.dumps({"status": "ERROR"}))
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(result)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        try:
            global M 
            cmd = json.loads(data)
            M.set_qps_target(cmd["qps_target"])
        except:
            self.wfile.write(json.dumps({"status": "ERROR"}))
            return

        self.send_response(200)
        self.end_headers()


def run():
    server = HTTPServer(("0.0.0.0", 2036), MonitorHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()
    #print M.get_stream_finished()
    #print M.get_cpu_utilization()
