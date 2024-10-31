# -*- coding:utf-8 -*-
import os
import time
import argparse
from functools import wraps

import control_knobs
import math
import workloads
import monitor
from setting import Setting
from strategy import *
import logging.handlers
import pcode_controller
from service.api import *

# Define workload latency target(ns)
LATENCY_TARGET = (2500, 2750)
# Control time interval(sec)
TIME_INTERVAL = 5
# Time for workload to be stable(sec)
WORKLOAD_INTERVAL = 10
# Time for configuration to be stable(sec)
CONFIG_INTERVAL = 15
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='closeloop.log',
                    filemode='w')

file = logging.handlers.TimedRotatingFileHandler("log/controller.log", 'D')
#fmt = logging.Formatter("%(asctime)s - %(pathname)s - %(filename)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s")  
fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  
file.setFormatter(fmt)  
file.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
CL = logging.getLogger('closeloop')
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
class Controller():
    def __init__(self, setting, monitor, pcode_controller, wl):
        self.setting = setting
        #self.strategy = strategy
        self.monitor = monitor
        self.pcode_controller = pcode_controller
        self.workload_client = wl
        self.resource_available_status = True
        self.workload_waiting = 0 
        self.system_time = time.time()

    def add_PR(self, name, loginfo):
        cfg = self.setting
        CL.info("Production workload: %s launched and registered with INFO:%s"% (name, str(loginfo).strip()))
        PR = workloads.workload.Workload(name, loginfo, cfg.PR_cores, cfg.PR_COS, cfg.control_knobs)
        cfg.add_PR(PR)

    def add_BE(self, name, loginfo):
        cfg = self.setting
        CL.info("Best effort workload: %s launched and registered with INFO:%s"% (name, str(loginfo).strip()))
        BE = workloads.workload.Workload(name, loginfo, cfg.BE_cores, cfg.BE_COS, cfg.control_knobs)
        cfg.add_BE(BE)

    def detatch_PR(self, PID):
        cfg = self.setting
        cfg.detach_PR(PID)

    def detatch_BE(self, PID):
        cfg = self.setting
        cfg.detach_BE(PID)

    def get_PR(self):
        cfg = self.setting
        l = []
        for pr in cfg.get_PR():
            info = pr.get_info()
            l.append(info)
        return {"PR": l}

    def get_BE(self):
        cfg = self.setting
        l = []
        for be in cfg.get_BE():
            info = be.get_info()
            l.append(info)
        return {"BE": l}

    def set_PR_cores(self, cores):
        cfg = self.setting
        cfg.set_PR_cores(cores)

    def set_BE_cores(self, cores):
        cfg = self.setting
        cfg.set_BE_cores(cores)

    def set_strategy(self, strategy):
        self.strategy = strategy

    def set_control_knobs(self, control_knobs):
        cfg = self.setting
        cfg.set_control_knobs(control_knobs)

    def get_control_knobs(self):
        cfg = self.setting
        cfg.get_control_knobs()

    def run(self):
        C = self.setting
        #S = self.strategy
        M = self.monitor
        PC = self.pcode_controller
        level = 0
        while True:
            self.system_time = time.ctime()
            # read from workload
            '''
            performance_issues = False
            for PR in C.get_PR():
                if PR.get_sla(): performance_issues = True
            '''
            if len(C.get_PR()) <1:
                time.sleep(TIME_INTERVAL)
                continue

            performance_function = lambda X: int(math.ceil(X)) if X > 0 else (math.floor(X))

            try:
                error_percentage = float(M.SLA_function("test"))
                level = performance_function(error_percentage)
            except Exception as e:
                print e.message
            #TODO can get control knob list based on model
            control_priority = ["hp_hwp", "lp_mba", "lp_cat"]

            pending_workload = self.workload_client.get_pending_workload()
            if pending_workload is not None:
                self.workload_waiting = int(pending_workload)
            if level > 0:
                CL.warning("Production workload performance issues detected!")
                level_return =  PC.increase_levels(control_priority, level)
                if level_return == level:
                    CL.info("Resource reallocation action to Best Effort workload finished.")
                    time.sleep(CONFIG_INTERVAL)
                    continue
                else:
                    # TODO send signel to user
                    try:
                        CL.warning("No more resource can be reallocated, suggest to do BE migration")
                        # TODO stop workload should be done by user
                        #BE_info = self.get_BE()
                        #last_BE_PID = BE_info["BE"][-1]["PID"]
                        #self.detatch_BE(last_BE_PID)
                        #self.workload_client.stop_workload(last_BE_PID)
                        self.resource_available_status = False
                        time.sleep(CONFIG_INTERVAL)
                        continue
                    except Exception:
                        CL.error("Unable to send messages")

            elif level < 0:
                if self.workload_waiting > 0:
                    # TODO add workload by user
                    CL.info("[Controller Recommendation]Send message to workload service to spawn more workloads from job launch queue")
                    r = self.workload_client.apply_for_workload(self.setting.get_BE_cores())
                    time.sleep(WORKLOAD_INTERVAL)
                    continue
                else:
                    #PC.decrease_levels(control_priority, level)
                    PC.decrease_level(control_priority)
                    self.resource_available_status = True
                    time.sleep(CONFIG_INTERVAL)
                    continue
            else:
                # if self.workload_waiting > 0:
                    # TODO add workload by user
                    # CL.info("[Controller Recommendation]Send message to workload service to spawn more workloads from job launch queue")
                    # r = self.workload_client.apply_for_workload(self.setting.get_BE_cores())
                    # time.sleep(WORKLOAD_INTERVAL)
                    # continue
                time.sleep(TIME_INTERVAL)
            '''
            fail_last_time = False
            performance_issues_last = performance_issues_now
            performance_issues_now = str(M.SLA_function("test"))
            if performance_issues_last == "0" and performance_issues_now == "0":
                performance_issues = "0"
            else:
                performance_issues = performance_issues_now
            if performance_issues == "-1":
                if fail_last_time:
                    time.sleep(TIME_INTERVAL)
                    continue
                else:
                    fail_last_time = True
            else:
                fail_last_time = False
            #TODO get whether there are workloads waiting to be launched from daemon
            pending_workload = self.workload_client.get_pending_workload()
            if pending_workload is not None:
                self.workload_waiting = int(pending_workload)
            if performance_issues == "1":
                CL.warning("Production workload performance issues detected!")
                if self.strategy.increase_level():
                #if 0:
                    CL.info("Resource reallocation action to Best Effort workload finished.")
                    time.sleep(CONFIG_INTERVAL)
                    continue
                else:
                    # TODO send signel to user
                    try:
                        CL.warning("No more resource can be reallocated, suggest to do BE migration")
                        #BE_info = self.get_BE()
                        #last_BE_PID = BE_info["BE"][-1]["PID"]
                        #self.detatch_BE(last_BE_PID)
                        # TODO stop workload should be done by user
                        #self.workload_client.stop_workload(last_BE_PID)
                        self.resource_available_status = False
                        time.sleep(CONFIG_INTERVAL)
                        continue
                    except Exception:
                        CL.error("Unable to send messages")
            elif performance_issues == "2":
                #CL.info("Resources available")
                if self.workload_waiting > 0:
                    # TODO add workload by user
                    CL.info("[Controller Recommendation]Send message to workload service to spawn more workloads from job launch queue")
                    r = self.workload_client.apply_for_workload(self.setting.get_BE_cores())
                    time.sleep(WORKLOAD_INTERVAL)
                    continue
                elif self.strategy.decrease_level():
                    self.resource_available_status = True
                    time.sleep(CONFIG_INTERVAL)
                    continue
            elif performance_issues == "0":
                if self.workload_waiting > 0:
                    if 1:
                        time.sleep(TIME_INTERVAL)
                        continue
                    CL.info("[Controller Recommendation]Send message to workload service to spawn more workloads from job launch queue")
                    # for more aggresive resource allocation, add workload here is allowed
                    #if not self.strategy.increase_level():
                    r = self.workload_client.apply_for_workload(self.setting.get_BE_cores())
                    time.sleep(WORKLOAD_INTERVAL)
                    continue
                time.sleep(TIME_INTERVAL)
                continue
            CL.info("Cannot get performance SLI (Service Level Indicator).")
            time.sleep(TIME_INTERVAL)
            '''


def createDaemon(obj):
    try:
        if os.fork() > 0: os._exit(0)
    except OSError, error:
        os._exit(1)
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0: os._exit(0)
    except OSError, error:
        os._exit(1)
    obj.run()

C = Setting(PR_COS='4', BE_COS='5', PR_cores='0-13,28-41', BE_cores='14-27,42-55', platform='skx')
#S = model_based_round_robin_controller.ModelBasedRoundRobinController(C.control_knobs, 100)
M = monitor.monitor.Monitor("test")
PC = pcode_controller.PcodeController(C.control_knobs)
PR = workloads.SPECjbb2015.SPECjbb2015(0, C.PR_cores, C.PR_COS, C.control_knobs)
# PR = workloads.workload.Workload('specjbb2015', 0, C.PR_cores, C.PR_COS, [C.PR_CAT, C.PR_MBA])
from workload_client import WorkloadClient
Client=WorkloadClient('127.0.0.1','2035')

CTL = Controller(C, M, PC, Client)

def get_controller():
    return CTL

if __name__ == "__main__":

    #################################################################################################
    # Parser config
    #################################################################################################
    parser = argparse.ArgumentParser(description="Run Controller Server")
    parser.add_argument("-D", "--daemon", dest="daemon", choices=['0', '1'], default=0,
                        help="Run this process as a daemon")
    parser.add_argument("-T", "--timeinterval", dest="timeinterval", help="Control time interval(sec)")
    parser.add_argument("-W", "--workloadinterval", dest="workloadinterval", help="Time for workload to be stable(sec)")
    parser.add_argument("-C", "--configinterval", dest="configinterval",
                        help="Time for configuration to be stable(sec)")
    args_dict = parser.parse_args()

    # Control time interval(sec)
    if args_dict.timeinterval:
        TIME_INTERVAL = int(args_dict.timeinterval)
    # Time for workload to be stable(sec)
    if args_dict.workloadinterval:
        WORKLOAD_INTERVAL = int(args_dict.workloadinterval)
    # Time for configuration to be stable(sec)
    if args_dict.configinterval:
        CONFIG_INTERVAL = int(args_dict.configinterval)

    # From here is test script
    # api.start_api_thread()
    '''
    C = Setting(PR_COS='4', BE_COS='5', PR_cores='0-13,28-41', BE_cores='14-27,42-55', platform='skx')
    S = model_based_round_robin_controller.ModelBasedRoundRobinController(C.BE_control_knobs, 100)
    M = monitor.monitor.Monitor("test")
    PR = workloads.SPECjbb2015.SPECjbb2015(0, C.PR_cores, C.PR_COS, C.PR_control_knobs)
    # PR = workloads.workload.Workload('specjbb2015', 0, C.PR_cores, C.PR_COS, [C.PR_CAT, C.PR_MBA])
    from workload_client import WorkloadClient
    Client=WorkloadClient('127.0.0.1','2035')

    S = Controller(C, S, M, Client)
    #C.add_PR(PR)
    #C.reset_resource(C.BE_control_knobs)
    '''
    from service.api import *
    start_api_thread()
    if args_dict.daemon == "1":
        CL.info("Running daemon mode")
        createDaemon(CTL)
    else:
        CTL.run()
