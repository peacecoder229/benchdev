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
class MonitorServer():
    def __init__(self, latency_target=(2500,2750), name='specjbb2015', result_path="/pnpdata/specjbb2015log/*/"):
        self.name = name
        self.last_hp_time = -1
        self.latency_target = latency_target #ns
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

    def set_latency_target(self,target):
        self.latency_target=target
        CL.info("SLO target is set to:%s sec" % str(target))

    def system_info(self):
        return {"cpu_utilization":self.get_cpu_utilization()} 


    def return_performance(self, input_file):
        try:
            output = os.popen('tail -n 20 %s|grep \'TotalPurchase\'' % input_file)
            result = output.read().split(',')[8]
            resultf = float(result)
            return resultf
        except:
            return -1

    def return_time(self, input_file):
        try:
            output = os.popen('tail -n 20 %s|grep \'Performance\'' % input_file)
            result = output.read().split('s:')[0]
            resultf = float(result)
            return resultf
        except:
            return -1

    def return_gc(self, input_file):
        try:
            output = os.popen('tail -n 1 %s |awk \'{print $2}\'' % input_file)
            result = output.read().split(':')[0]
            resultf = float(result)
            return resultf
        except:
            return -1

    def SLA_function(self):
        performance = self.return_performance(self.result_path + 'controller.out')
        hp_time = self.return_time(self.result_path + 'controller.out')
        gc_time = self.return_gc(self.result_path + 'gc.log')
        stream_instance = self.get_stream_instance()
        util = self.get_cpu_utilization()
        stream_count = self.get_stream_finished()
        CL.info("System CPU utilization: %s" % util)
        CL.info("Stream instance:%s" % stream_instance)
        CL.info("Stream finished:%s" % stream_count)
        CL.info("Production workload performance data in track at application time:%s sec" % hp_time)
        CL.info("JVM GC kicked in at application time:%s sec" % gc_time)
        if performance == -1 or hp_time == self.last_hp_time:
            CL.warning("Cannot get performance data! Will retry in 5 sec.")
            return 0
        self.last_hp_time = hp_time
        error_percentage = float(performance)/self.latency_target[1] - 1
        if error_percentage > 10:
            CL.warning("Abnormal latency result(outlier) detected! May caused by GC: %s." %gc_time)
            return 0
        elif error_percentage > 0:
            CL.warning(
                "Latency issues detected, SLI(Service Level Indicator): %s, SLO_Target: latency in %s" % (performance, self.latency_target))
            return error_percentage
        elif error_percentage < 0:
            CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: latency in %s" % (performance, self.latency_target))
            return error_percentage
        CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: latency in %s" % (performance, self.latency_target))
        return 0

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
            #output = os.popen('tail -5 %s|grep requests | awk \'{print $1}\'' % input_file)
            output = os.popen('tail %s|grep \'requests per second\' | awk \'{print $1}\'' % input_file)
            result = output.read()
            if result == '':
                return -1
            l = result.strip().split('\n')
            fltl = [float(i) for i in l]
            c = min(fltl)
            #c = sum(fltl)/len(fltl)
            return c
        except:
            return -1

    def SLA_function(self):
        performance = self.return_performance(self.result_path + 'redis*.log')
        util = self.get_cpu_utilization()
        stream_instance = self.get_stream_instance()
        stream_count = self.get_stream_finished()
        CL.info("System CPU utilization: %s" % util)
        CL.info("Stream instance:%s" % stream_instance)
        CL.info("Stream finished:%s" % stream_count)
        error_percentage = 1 - float(performance)/self.qps_target[1]
        if performance == -1:
            CL.warning("Cannot get performance data! Will retry in 5 sec.")
            return -1
        elif performance < self.qps_target[0]:
            CL.warning(
                "QPS issues detected, SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
            return error_percentage
        elif performance > self.qps_target[1]:
            CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
            return error_percentage
        CL.info("Achieved SLO (Service Level Objective), SLI(Service Level Indicator): %s, SLO_Target: QPS in %s" % (performance, self.qps_target))
        return 0

type_dic = {'specjbb2015':MonitorServer(), 'redis':MonitorServerRedis()}
type = None

class MonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # self.send_response(200)
            global type
            global type_dic
            name = self.path.split('?')[0]
            if name == '/get_workload_performance':
                if type is None:
                    return -1
                M = type_dic[type] 
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
            global type_dic
            global type
            cmd = json.loads(data)
            if cmd["name"]=='specjbb2015':
                type = 'specjbb2015' 
                type_dic[type].set_latency_target(cmd["latency_target"])
            if cmd["name"]=='redis':
                type = 'redis' 
                type_dic[type].set_qps_target(cmd["qps_target"])
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
    #print MonitorServerRedis().return_performance("/home/dianjuns/dynamic_resource_control/redis_output/" + 'redis*.log')
