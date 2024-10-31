# -*- coding: utf-8 -*-
import os
import time
import urllib
import requests
import json

class MonitorClient():
    def __init__(self, ip, port):
        self.ip = ip
        self.port =port

    def set_qps_target(self,target, name="redis"):
        r = requests.post("http://%s:%s/set_qps_target"%(self.ip, self.port),json={"qps_target":target, "name":name})
    
    def set_latency_target(self,target, name="specjbb2015"):
        r = requests.post("http://%s:%s/set_latency_target"%(self.ip, self.port),json={"latency_target":target, "name":name})

    def get_workload_performance(self,pid):
        f = urllib.urlopen("http://%s:%s/get_workload_performance?%s"%(self.ip,self.port,pid))
        r = f.read()
        #r = requests.get("http://%s:%s/get_workload_performance?%s"%(self.ip,self.port,pid))
        return r

if __name__ == "__main__":
    C = MonitorClient('127.0.0.1',2036)
    print C.set_qps_target((2500,2750))
    print C.get_workload_performance(0)
    #C.set_latency_target((2500,2750))

