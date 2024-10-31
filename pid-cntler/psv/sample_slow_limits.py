import components.socket as socks
import pm.pmutils.tools as t
import time
from components import ComponentManager
s0 = socks.getAll()[0]

def sample_pbm_limit(duration):
    start_time = time.time()
    while True:
        cur_time = time.time()
        if cur_time < start_time + duration:
            core_limit = s0.pcudata.global_slow_limits_pbm_limit_0
            clm_limit = s0.pcudata.global_slow_limits_pbm_limit_2
            print "%.2f, %d, %d" %(cur_time-start_time, core_limit, clm_limit)
        else:
            break