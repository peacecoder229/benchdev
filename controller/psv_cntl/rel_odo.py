import components.socket as socks
import pm.pmutils.tools as t
import pm.pmdebug as d
import time
import pm.thermal as t
from components import ComponentManager
from itpii.datatypes import BitData
s0 = socks.getAll()[0]

def initialize():
	print "Preparing socket for rel odometer testing"
	s0.pcudata.rgb_ia_c = 22296
	s0.pcudata.rgb_ia_v_stress = 11040
	s0.pcudata.rgb_ia_t_cel_stress = 420
	s0.pcudata.rgb_clr_c = 22296
	s0.pcudata.rgb_clr_v_stress = 10240
	s0.pcudata.rgb_clr_t_cel_stress = 380
	s0.uncore0.pcu_cr_turbo_activation_ratio=7
	t.set_all_dfx(70)
	s0.pcudata.dfx_pkg_c1e_disable=1
	d.pkgc.set_pkgc_limits_dfx_ctrl(1,1)

def sample(nsamples):
	sample_last = BitData(64)
	sample_new = BitData(64)
	delta = BitData(64)
	sample_last = s0.pcudata.rgb_core0_stress_1 
	sample_last = sample_last << 32
	sample_last = sample_last + s0.pcudata.rgb_core0_stress_0
	samples = 0
	while (samples < nsamples):
		sample_new = s0.pcudata.rgb_core0_stress_1 
		sample_new = sample_new << 32
		sample_new = sample_new + s0.pcudata.rgb_core0_stress_0
		vid = s0.pcudata.global_gvfsm_current_slice_voltage_0
		delta = sample_new - sample_last
		sample_last = sample_new
		samples = samples+1
		print "%g, %f" %(delta/2.0**44, float(vid)/2.0**13)
		time.sleep(1)
	
def print_constants():
	print s0.pcudata.rgb_ia_c
	print s0.pcudata.rgb_ia_v_stress
	print s0.pcudata.rgb_ia_t_cel_stress
	print s0.pcudata.rgb_clr_c
	print s0.pcudata.rgb_clr_v_stress
	print s0.pcudata.rgb_clr_t_cel_stress