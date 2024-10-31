import sys
import os
import time
from strategy.pid import PID
from control_knobs.mba import MBA
from strategy.MA_pid import MAPID
from ipc_checker import IPCChecker

INTERVAL = 5

def return_performance(input_file='pqos_output/pqos.log'):
    try:
        output = os.popen('tail -n 2 %s' % input_file)
        result_h = output.readline().split()
        result_h_mb = result_h[4]
        result_h_ipc = result_h[1]
        result_l = output.readline().split()
        result_l_mb = result_l[4]
        result_l_ipc = result_l[1]
        # result = output.read().split(',')[10] # P95
        return float(result_h_mb), float(result_l_mb), float(result_h_ipc), float(result_l_ipc)
    except:
        return -1, -1, -1, -1

def start_pqos(hp_core='[0-13,28-41]', lp_core='[14-27,42-55]', path='pqos_output/pqos.log'):
    cmd = 'pqos -m all:%s,%s -i 50 > %s &'%(hp_core, lp_core, path)
    os.system(cmd)

def run(qps_target, static_flag=0, lp_core='14-27,42-55'):
    #c = PID()
    c = MAPID()
    m = MBA(0, 5, lp_core)
    ipc_c = IPCChecker()
    start_pqos()
    print "hp_mb","lp_mb","hp_ipc","lp_ipc","level_now"
    while 1:
        hp_mb,lp_mb,hp_ipc,lp_ipc = return_performance()
        if hp_mb==-1 and lp_mb==-1:
            time.sleep(INTERVAL)
            continue
        if static_flag:
            print hp_mb,lp_mb,hp_ipc,lp_ipc,m.get_level()
            time.sleep(INTERVAL)
            continue
        if not static_flag:
            error_percentage =  1.0 - hp_mb/qps_target 
            l = c.e2l(error_percentage)
            print ",".join([str(hp_mb),str(lp_mb),str(hp_ipc),str(lp_ipc), str(m.get_level()),str(error_percentage),str(l)])
            if ipc_c.check(hp_ipc):
                print "ipc acceptable" 
                time.sleep(INTERVAL)
                continue
            m.change_levels(l)
            time.sleep(INTERVAL)
            continue

if __name__ == "__main__":
    qps = int(sys.argv[1])
    static_flag = int(sys.argv[2])
    run(qps, static_flag)
