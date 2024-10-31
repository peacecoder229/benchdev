#!/usr/bin/python

from __future__ import print_function
import time
import components.socket as socks
import misc.coverage.pmonutil as pu
import itpii
import PID

itp = itpii.baseaccess()
s0 = socks.getAll()[0]



#pointers to registers. Socket0 only.
#CMSegr registers
#s0.uncore0.search('cmsegr_spare_cfg')

#RPQ_OCC perfmons
rpqOccCounters=s0.uncore0.search('imc._c._pmoncntr_1')

#BW perfmons 
bwCounters=s0.uncore0.search('imc._c._pmoncntr_0')

def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split('.'), obj)

def setup():
 global rpqOccPerfmon
 global bwPerfmon
 global pid
 global cmsegrDelay
 
 pid = PID.PID(-0.4, -0.8, 0)
 pid.setWindup(3)
 pid.setSetPoint(4)
 cmsegrDelay=0
 
 rpqOccPerfmon=[]
 bwPerfmon=[]
 #Setup perfmons and start counting
 pu.main()
 
 for imc in range(2):
  imcstr = 'imc%d'%imc
  getattr(s0.pmons,imcstr).clearConfigs()
  for channel in range(3):
   channelstr = 'c%d'%channel
   bwPerfmon.append(deepgetattr(s0.pmons,imcstr+'.'+imcstr+'_'+channelstr+'.events.cas_count_1.all_0xf').setup())
   #s0.pmons.imc0.imc0_c0.events.rpq_occupancy.setup()
   rpqOccPerfmon.append(deepgetattr(s0.pmons,imcstr+'.'+imcstr+'_'+channelstr+'.events.rpq_occupancy').setup())
  deepgetattr(s0.pmons,imcstr).start()
  
 #Setup cores 8-15 as CLOS 1 (low priority)
 """
 itp.halt()
 ncores=16
 for core in itp.cores[0:ncores]:
  if len(core.threads)>0:
   core.threads[0].msr(0xC8F, 0)
 for core in itp.cores[ncores:2*ncores]:
  if len(core.threads)>0:
   core.threads[0].msr(0xC8F, 1<<32)
 itp.go()
 """
 
def mem_bw(counterHandle, lastVal, lastTime):
 newVal = counterHandle.getValue()
 newTime = time.time()
 bw = ((newVal-lastVal)*8/(float(newTime)-lastTime)/1e9/2.4*100)
 return [bw, newVal, newTime]
 
def rpq_occ(counterHandle, lastVal, lastTime):
 newVal = counterHandle.getValue()
 newTime = time.time()
 occ = (newVal-lastVal)*2/(float(newTime)-lastTime)/1e9/2.4
 return [occ, newVal, newTime]

def loop(func, counterList, interval):
 global pid
 global cmsegrDelay
 
 lastVal=[1]*len(counterList)
 lastTime=[1]*len(counterList)
 while 1:
  vector=[]
  i=0
  for counter in counterList:
   [value, lastVal[i], lastTime[i]]=func(counter, lastVal[i], lastTime[i])
   vector.append(value)
   i=i+1
  pid.update(max(vector))
  output=pid.output
  cmsegrDelay += int(output)
  cmsegrDelay = min(max(0,cmsegrDelay),0xf)
  setLowPriorityDelay(cmsegrDelay)
  #print ["{0:0.2f}".format(ele) for ele in vector]
  #print "%.2f %.2f"%(pid.output, cmsegrDelay)
  print("%2.2f "%cmsegrDelay, end="")
  time.sleep(interval)

def run():
 loop(rpq_occ, rpqOccPerfmon, 0.1)
 #loop(mem_bw, bwPerfmon, 1)
 
def setLowPriorityDelay(val):
 for registerName in s0.uncore0.cbological.search('cmsegr_spare_cfg'):
  s0.uncore0.cbological.writeregister(registerName, val<<4)
