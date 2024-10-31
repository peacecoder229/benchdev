#!/usr/bin/env python

import components.socket as socks
import pm.pmutils.tools as t
import pm.pmdebug as d
import time
from components import ComponentManager
import math
s0 = socks.getAll()[0]
#sv = ComponentManager()

def lpf_debug(coreid, duration):
 start_time = time.time()
 print "time, hcpm_ratio, hwpm_dyn_sw_filtered_ratio, per_core_epb_policy"
 while True:
	cur_time = time.time()
	if cur_time < start_time + duration:
		hcpm_ratio = getattr(s0.pcudata, "hcpm_ratio_%d" %coreid)
		hwpm_dyn_sw_filtered_ratio = getattr(s0.pcudata, "patch_hwpm_dyn_sw_filtered_ratio_%d" %coreid)
		per_core_epb_policy = getattr(s0.pcudata, "per_core_epb_policy_%d" %coreid)
		print "%.2f, %d, %.2f, %d" %(cur_time, hcpm_ratio, hwpm_dyn_sw_filtered_ratio/2.0**24, per_core_epb_policy)
	else:
		break

def write_epp_oob(epp=128, socketid=0):
	socket = socks.getAll()[socketid]
	
	for thread_epp in socket.pcudata.search('hwpm_thread_epp_target'):
		thread_epp_reg = socket.pcudata.getregisterobject(thread_epp)
		thread_epp_reg.write(epp)
	
	for core_epp in socket.pcudata.search('hwpm_core_epp_target'):
		core_epp_reg = socket.pcudata.getregisterobject(core_epp)
		core_epp_reg.write(epp)
	socket.pcudata.hwpm_init_done=0
	

	
	
def set_activity_window(val):
 for core in range(28):
  aw = s0.pcudata.getreg('hwpm_thread_activity_window_target_%d' %core)
  aw.write(val)
def get_activity_window_all():
 for core in range(28):
  print s0.pcudata.getreg('hwpm_thread_activity_window_target_%d' %core)
def ppo_budget_show():
 ppo_budget_threshold = s0.uncore0.pcudata(0xca5c)
 print 'ppo_budget_threshold: %d' %ppo_budget_threshold
 pkg_pbm_limit = s0.pcudata.getreg('global_slow_limits_pbm_limit_0')
 print 'pkg_pbm_limit: %d' %pkg_pbm_limit
 #sv.socket0.pcudata.pbm_max_r_factor = 0x100
 max_r_factor = s0.pcudata.getreg('pbm_max_r_factor')
 print 'max_r_factor: %f' %(float(max_r_factor)/2.0**8)
 R = s0.pcudata.getreg('pbm_total_ratio_scaled')
 print 'R: %f' %(float(R)/2.0**8)
 scalability = not s0.pcudata.global_bios_mbx_pcu_misc_config.core_scalability_disable
 print "Scalability: %d" % scalability
 print "min ratio:"
 for id in range(28):
  min = s0.pcudata.getreg('hwpm_min_target_%d' %id)
  print "%.2f " % (float(min)/2.0**8),
 print
 total_min = s0.pcudata.getreg('pbm_total_min_required')
 print "Sum min %.2f" % (float(total_min)/2.0**8)
 total_min_inv = s0.pcudata.getreg('pbm_total_min_inv')
 print "Sum min inv %.2f" % (float(total_min_inv)/2.0**23)
 if scalability:
  print "epp:"
  for id in range(28):
   eff = s0.pcudata.getreg('hwpm_core_epp_target_%d' %id)
   print "%d " %eff,
 else:
  print "efficiency:"
  for id in range(28):
   eff = s0.pcudata.getreg('pbm_r_metric_%d' %id)
   print "%d " %eff,
 print
 total_eff = s0.pcudata.getreg('pbm_r_total')
 print "Total eff: %.2f" %total_eff
 total_eff_inv = s0.pcudata.getreg('pbm_efficiency_total_inv')
 total_eff_inv_rp = s0.pcudata.getreg('pbm_efficiency_total_inv_rp')
 print "Total eff inv %f" % (float(total_eff_inv)/2.0**total_eff_inv_rp)
 print "filtered ratio limit:"
 for id in range(28):
  fil_ratio = s0.pcudata.getreg('global_slow_limits_per_core_pbm_limit_%d' %id)
  print "%d " %fil_ratio,
 print
def ppo_target_show(id):
 print "P1: %d" %s0.uncore0.pcu_cr_platform_info.max_non_turbo_lim_ratio
 print "disable_eet: %d" %s0.pcudata.disable_eet
 print "pcu_cr_dynamic_perf_power_ctl_cfg.eet_override_enable: %d" %s0.uncore0.pcu_cr_dynamic_perf_power_ctl_cfg.eet_override_enable
 print "pcu_cr_power_ctl1.ee_turbo_disable: %d" %s0.uncore0.pcu_cr_power_ctl1.ee_turbo_disable
 s0.pcudata.showsearch('per_core_epb_policy_%d'%id)
 s0.pcudata.showsearch('core_c0.*_.*_delta_%d'%id)
 s0.pcudata.showsearch('core_stall.*_.*_delta_%d'%id)
 s0.pcudata.showsearch('core_eec.*_.*_delta_%d'%id)
 s0.pcudata.showsearch('eet_core_scalability.*_%d'%id)
 s0.pcudata.showsearch('eet_scalability_min_offset')
 
 if int(s0.pcudata.io_pm_enable) == 1 or int(s0.uncore0.pcu_cr_misc_pwr_mgmt2.out_of_band == 1):
  print "HWP Core %d pstate request: %d" % (id, int(s0.pcudata.getbypath('core_auto_p_target_%d' %id))>>8)
  fsindex = s0.pcudata.getreg('eet_core_freq_scale_%d' %id)
  epb_policy=int(s0.pcudata.getreg('per_core_epb_policy_%d'%id))
  freq_scale_factor=ppo_target_freq_scale_table(fsindex+16*epb_policy)
  print "freq_scale_factor : %0.2f" %(float(freq_scale_factor)/2.0**12)
  s0.pcudata.showsearch('gpss_hwp_pstate_target_%d'%id)
  s0.pcudata.showsearch('gpss_core_pstate_target_%d'%id)
 else:
  print "legacy Core %d pstate request: %d" % (id, s0.pcudata.getbypath('io_core_p_req_core%d.p_state_req' %id))
  s0.pcudata.showsearch('eet_core_freq_scale_%d' %id)
  freq_scale_factor = s0.pcudata.getreg('eet_core_freq_scale_%d' %id)
  print "freq_scale_factor : %0.2f" %(float(freq_scale_factor)/2.0**12)
  s0.pcudata.showsearch('preq_core_pstate_target_%d'%id)
  s0.pcudata.showsearch('gpss_core_pstate_target_%d'%id)

def ppo_target_freq_scale_table(id=None):
 if id == None:
  for i in range(64):
   freq_scale_factor = s0.pcudata.getreg('eet_freq_scale_table_%d' %i)
   print "freq_scale_factor_%2d: %0.2f" % (i, float(freq_scale_factor)/2.0**12)
 else:
  freq_scale_factor = s0.pcudata.getreg('eet_freq_scale_table_%d' %id)
  return freq_scale_factor

def print_activity_window():
 #activity window
 #s0.pcudata.hwpm_thread_activity_window_target_0=0x281
 #get bits
 aw= s0.pcudata.hwpm_thread_activity_window_target_0
 aw_significand = t.convert.getBits2(s0.pcudata.hwpm_thread_activity_window_target_0,"6:0")
 print 'activity window 0x%x'%s0.pcudata.hwpm_thread_activity_window_target_0
 print 'significand = %d'%aw_significand
 aw_exponent = t.convert.getBits2(s0.pcudata.hwpm_thread_activity_window_target_0,"9:7")
 print 'exponent = %d'%aw_exponent
 aw = aw_significand * 10.0**aw_exponent
 print "%.3f ms"%(aw/1000.0)

def aw_to_us(val):
 aw_significand = t.convert.getBits2(val,"6:0")
 print 'significand = %d'%aw_significand
 aw_exponent = t.convert.getBits2(val,"9:7")
 print 'exponent = %d'%aw_exponent
 aw = aw_significand * 10.0**aw_exponent
 print "%.3f ms"%(aw/1000.0)
 
def us_to_activity_window(val):
 # get an activity window in micro seconds and print an activity window code for it
 
 exponent = math.floor(math.log10(val))
 significand = val/(10.0**exponent)
 
 while 1: 
  if (significand <> math.floor(significand) and exponent>0):
   exponent -=1
   significand = val/(10.0**exponent)
  else:
   break
 if significand > 0x7f:
  exponent += 1
  significand = val/(10.0**exponent)

 if exponent > 0x8 or significand > 0x7f or significand <> math.floor(significand):
  print "Could not find an exact activity window code. Check that the us value is within range and precision"
  #return -1
 aw = (int(exponent) << 7) | int(significand)
 print "exponent = %f"  %exponent
 print "significand = %f"  %significand
 print "activity window = 0x%x" %aw
 return aw
 
def av_util():
 t.histo.histo(s0.pcudata.hcpm_util_ave_0, runtime=1, showSamples=True)

def showall():
 #activity window
 print_activity_window()
 #bin2float
 #t.convert.bin2float(0xed9,"U13.1.12")
 #ubps_factor: t.histo.histo(s0.pcudata.hwpm_ubps_factor_0, runtime=2, showSamples=True)
 t.histo.histo(s0.pcudata.hcpm_c0_th0_res_dlta_0, runtime=1, showSamples=True)
 #inst utilization:  
 t.histo.histo(s0.pcudata.hcpm_util_0, runtime=1, showSamples=True)
 #average utilization: 
 t.histo.histo(s0.pcudata.hcpm_util_ave_0, runtime=1, showSamples=True)
 #epp: 
 t.histo.histo(s0.pcudata.hwpm_thread_epp_target_0, runtime=1, showSamples=True)
 #gain: 
 t.histo.histo(s0.pcudata.hwpm_ubps_gain_0, runtime=1, showSamples=True)
 print "gain=%.2f"%(s0.pcudata.hwpm_ubps_gain_0*1.0/(2.0**12))
 #ratio_decay: 
 t.histo.histo(s0.pcudata.hwpm_ubps_ratio_decay_0, runtime=1, showSamples=True)
 #hcpm_timer: 
 #t.histo.histo(s0.pcudata.hcpm_timer, runtime=1, showSamples=True)
 #hcpm_ratio: 
 s0.pcudata.hcpm_ratio_0
 #d.pstates.ratio_resolving()

