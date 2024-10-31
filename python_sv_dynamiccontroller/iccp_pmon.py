def ICCPinitialize():
	sv.refresh()
	sv.sockets.pcudata.calibrated_icc_hysteresis_expiration_interval=0
	sv.sockets.pcudata.iccp2_min_license_level=1
	import misc.coverage.pmonutil as pu
	import pm.peci_dfx as pdfx
	import time
	pu.main()
	pmonlist=[]
	for socketid in range(2):
	 for coreid in range(16):
	  for threadid in range(2):
	   core = getattr(sv.sockets[socketid].pmons.core,'core%d'%coreid)
	   thread = getattr(core,'thread%d'%threadid)
	   pmon=thread.events.icc_protector.throttle_0x6.setup()
	   pmon.start()
	   pmonlist.append(pmon)

def ICCPsample():
	counter=0
	for pmon in pmonlist:
	 curtime=time.time()
	 counterval=pmon.getValue()
	 print('%d, %f, %d') %(counter,curtime,counterval)
	 counter+=1

def ICCPtrigger():
 lastpmonvals=[0]*64
 lastpmontimes=[0]*64
 while (1):
	 for i in range(64):
	  newval = pmonlist[i].getValue()
	  newtime = time.time()
	  if newval == 0:
	   newval = lastpmonvals[i]
	  trigger(newval,lastpmonvals[i],newtime,lastpmontimes[i])
	  lastpmonvals[i]=newval
	  lastpmontimes[i]=newtime
  
def trigger(newval, oldval, newtime, oldtime):
 slope = (newval-oldval)/(newtime-oldtime)/2.8e9
 print('slope = %.2f') %slope
 if slope > 0.10:
  print "triggering"
  pdfx.rdPkgConfig(0,53,0)
