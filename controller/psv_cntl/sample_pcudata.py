import components.socket as socks
import pm.pmutils.tools as t
import time
from components import ComponentManager
s0 = socks.getAll()[0]

def sample(duration, obj):
	start = time.time()
	cur = time.time()
	list = []
	nsamples=0
	while cur < start + duration:
		sample = obj.read()
		cur = time.time()
		str = "%.2f, %x" %(cur, sample)
		list.append(str)
		nsamples = nsamples+1
	print list
	print nsamples
		
