# -*- coding: utf-8 -*-
import os
import time
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import json
import subprocess
import signal
import requests
import logging
import logging.handlers


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='workload.log',
                    filemode='w')

file = logging.handlers.TimedRotatingFileHandler("log/workload.log", 'D')
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
#fmt = logging.Formatter("%(asctime)s - %(pathname)s - %(filename)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s")
file.setFormatter(fmt)
file.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
CL = logging.getLogger('workload')
CL.addHandler(console)
CL.addHandler(file)

port_start=7777

def start_redis(cores):
    hp_cores = '0-13,28-41'
    # hp_cores = get_hp_cores()
    global port_start
    name = 'redis' + str(time.time())
    s_cmd = 'nohup taskset -c %s redis-server --port %s &'% (hp_cores, port_start)
    c_cmd = 'taskset -c %s redis-benchmark -t set -n 100000 -c 20 -l -p %s > redis_output/redis%s.log &'% (hp_cores, port_start, port_start)
    os.system(s_cmd)
    os.system(c_cmd)
    p = os.popen('ps aux |grep *:%s | awk \'{print $5}\' | head -1'% port_start)
    pid = p.readline()
    port_start+=1
    return name, pid

def start_stream(cores):
    docker_name = "stream" + str(time.time())
    cmd = "docker run --cpuset-cpus=%s -d --name %s stream:loop 2>&1 &" % (cores, docker_name)
    p = os.popen(cmd)
    pid = p.readline()
    return docker_name, pid
    
def start_specjbb2015(cores):
    hp_cores = '0-13,28-41'
    path = "/pnpdata/specjbb2015log"
    os.system('mkdir -p %s'%path)
    # hp_cores = get_hp_cores()
    # path = get_work_path()
    os.system("rm -rf %s/*/controller.out"%path)
    os.system("rm -rf %s/*/gc.log"%path)
    docker_name = "SPECjbb2015" + str(time.time())
    cmd = "docker run --cpuset-cpus=%s -v %s:/result specjbb2015:g1gc 2>&1 &"%(hp_cores, path)
    f = os.popen(cmd)
    pid = f.readline()
    return docker_name, pid

workload_list = []
workload_lp = {"stream":start_stream}
workload_hp = {"specjbb2015":start_specjbb2015, "redis":start_redis}

def register(name, pid, type='BE', ip='127.0.0.1', port=2017):
    #TODO http service
#    CL.info("register workload %s")%pid
    print requests.post("http://%s:%s/workload/%s" % (ip, port, type),data=json.dumps({'name': name, 'PID': pid, 'type': type}))


def stop_workload(id, type = "docker_id"):
    if type == "docker_id":
        cmd = "docker rm -f %s 2>&1" % id
    else:
        cmd = "kill -9 %s" % id
    p = os.popen(cmd)
    result = p.readlines()[0]
    return result
'''
def add_workload(type):
    global workload_lp
    global workload_list
    if type in workload_lp.keys():
        workload_list.append(type)
        return True
    else:
        return False
'''
def start_workload(cores):
    global workload_lp
    global workload_list
    obj = workload_list.pop()
    return workload_lp[obj](cores)

def pending_workload():
    global workload_lp
    global workload_list
    return len(workload_list)

class Cmd2Action():
    def __init__(self, cmd):
        self.cmd = cmd

    def action(self):
        request = {
            # "/" : self.__load_index(),
            "/get_pending_workload": self.get_pending_workload,
            "/stop_workload": self.stop_workload,
            "/apply_for_workload": self.apply_for_workload,
            "/add_workload": self.add_workload
        }
        return request[self.cmd.split("?")[0]]()

    def get_pending_workload(self):
        return pending_workload()

    def stop_workload(self):
        pid = self.cmd.split("?")[1]
        #CL.info("Stop workload %s")%pid
        try:
            # result = os.kill(pid)
            result = stop_workload(pid)
            return result
        except OSError, e:
            return e

    def apply_for_workload(self):
        if self.get_pending_workload():
            cores = self.cmd.split("?")[1]
            name, pid = start_workload(cores)
            register(name, pid)
            return True
        else:
            return False

    def add_workload(self):
        global workload_lp
        global workload_list
        type = self.cmd.split("?")[1]
        cores = self.cmd.split("?")[-1]
        CL.info("Add workload %s"%type)
        if type in workload_hp.keys():
            name,pid = workload_hp[type](cores)
            register(name, pid, type="PR")
            CL.info("register finished")
            return True
        if type in workload_lp.keys():
            workload_list.append(type)
            return True
        else:
            return False

class WebAPIRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # self.send_response(200)
            C2A = Cmd2Action(self.path)
            result = C2A.action()
        except Exception as e:
            print e.message
            self.wfile.write(json.dumps({"status": "ERROR"}))
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(result)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        try:
            cmd = json.loads(data)
        except:
            self.wfile.write(json.dumps({"status": "ERROR"}))
            return

        self.send_response(200)
        self.end_headers()


def run():
    server = HTTPServer(("0.0.0.0", 2035), WebAPIRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    run()
    #start_specjbb2015(1)
