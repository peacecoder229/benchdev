from threading import Thread
from controller import *
import requests
import workload_client
from service.api import *
import logging

# Initialize controller and start

# Setting initialize
C = Setting(PR_COS='4', BE_COS='5', PR_cores='0-13,28-41', BE_cores='14-27,42-55', platform='skx')
# Strategy initialize
S = model_based_round_robin_controller.ModelBasedRoundRobinController(C.control_knobs, 100)
# Monitor initialize
M = monitor.monitor.Monitor("test")
# WorkloadClient initialize
WC = workload_client.WorkloadClient('127.0.0.1', '2035')

S = Controller(C, S, M, WC)
start_api_thread()

CL = logging.getLogger('closeloop')


#if args_dict.daemon == "1":
#    CL.logger.info("Running daemon mode")
#    createDaemon(S)
#else:
#    S.run()
thread = Thread(target=S.run)
thread.start()

# register PR could be done by http
#pid = "60132"
#S.add_PR("specjbb2015", pid)
WC.add_workload("specjbb2015")

# define how to monitor performance
MC = monitor.monitor_client.MonitorClient('127.0.0.1', '2036')
S.monitor.set_SLA_function(MC.get_workload_performance)

# add BE workload to test controller
for i in range(50):
    WC.add_workload("stream")
