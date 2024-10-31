import time
import components.socket as socks
s0 = socks.getAll()[0]

def sample():
 c0_residency_start = s0.pcudata.io_c0_residency_core2
 io_power_counter_start = s0.pcudata.io_power_counter_core2
 time.sleep(1)
 c0_residency_end = s0.pcudata.io_c0_residency_core2
 io_power_counter_end = s0.pcudata.io_power_counter_core2
 print "%d, %d" %(c0_residency_end-c0_residency_start, io_power_counter_end-io_power_counter_start)