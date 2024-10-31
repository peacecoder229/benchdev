#
# Python environment setup and DLL import
#

import os, time, sys, traceback
import clr

sys.path.append(r'c:\intel\dal')
# Import the public assemblies 
clr.AddReference("Intel.DAL.MasterFrame")
clr.AddReference("Intel.DAL.Services.Job")
clr.AddReference("Intel.DAL.Builders.TapCmdReg")
clr.AddReference("Intel.DAL.Builders.ExecutionControl")
clr.AddReference("Intel.DAL.Builders.State")
clr.AddReference("Intel.DAL.Common.IState.Bar")
clr.AddReference("Intel.DAL.Services.TargetTopology") 
clr.AddReference("Intel.DAL.Services.BreakManager")
# Import private assemblies (this is required for CPython / Python .NET only)
clr.AddReference("Intel.DAL.Services.TargetTopology.Impl")
clr.AddReference("Intel.DAL.Services.Job.Impl")
clr.AddReference("Intel.DAL.Services.Job.Impl.JobEngine")
clr.AddReference("Intel.DAL.Builders.TapCmdReg.Impl")
clr.AddReference("Intel.DAL.Builders.State.Impl")
clr.AddReference("Intel.DAL.Builders.ExecutionControl.Impl")
clr.AddReference("Intel.DAL.Services.BreakManager.Impl ")


from itpii import baseaccess
itp = baseaccess()
try:
    itp.halt()
except:
    pass

# Import the public assemblies and types used in this example
from Intel.DAL.MasterFrame import MasterFrame

from Intel.DAL.Services.TargetTopology import (
    IServiceTargetTopology, LNodeThread
)

from Intel.DAL.Services.BreakManager import IServiceBreakManager

from Intel.DAL.Services.Job import (
    IJobService, EExecutionStatus, IExecutionReceipt
)

from Intel.DAL.Builders import (
    IBuilderTapCmdReg, IBuilderState, IBuilderExecutionControl
)


# Init global variables
devices = {}
jobService = None


#
# Get services using MasterFrame and get a devices for all threads from Topology
# (ie devices to execute the job(s) against)
#
def setup():
    global devices
    global jobService
    print("setup...")
    mf = MasterFrame()
    jobService = mf.GetService[IJobService]()
    topologyService = mf.GetService[IServiceTargetTopology]()
    threads = topologyService.LogicalRoot.FindRelatedLNodeThreads(1)
    for thread in threads:
        devices[thread.Name] = thread
    print("setup done.")
    #print(devices)

def runJobMultipleStateRead(device, iterations=100):
    lNode = devices[device]
    # Create Job
    job = jobService.CreateJob("READ_MULTIPLE_STATE_EXAMPLE")
    # Obtain Builders
    bldrTapCmd = jobService.GetBuilder(IBuilderTapCmdReg, job.Main)
    bldrState = jobService.GetBuilder(IBuilderState, job.Main)
    # Add Operations
    #bldrTapCmd.RegRead("idcode")
    #bldrTapCmd.RegRead("tapstatus")
    bldrState.Read("eax")
    bldrState.Read("ebx")
    #bldrState.Write("eax", BitData(32, 0xfeedbeef))
    #bldrState.Read("eax")
    #bldrState.Read("rax")
    #bldrState.Read("rbx")
    #bldrState.Read("rcx")
    #bldrState.Read("cr0")
    #bldrState.Read("msr._address(0x1df)")
    #bldrState.Read("memory32._address(0x100)")
    # Execute this job
    start = time.time()    
    for i in range(iterations):
        jobReceipt = job.Execute(lNode).WaitCompletion()
        if(jobReceipt.Status != EExecutionStatus.Completed):
            print("Job failed to complete on iteration %d"%i)
            # ---------------------------------
            # example use snl string to obtain values
            # ---------------------------------
            #print "Iteration %d:"%i
            #iState = jobReceipt.GetData()
            #print "eax = " + iState.Read("eax").ToString()
            #print "msr = " + iState.Read("msr").ToString()
        #else:
        #    print "job failed to complete"
    print("Job took %s seconds to complete %d iterations"%(time.time()-start, iterations))
#
# Lets do this example
#
try:
	iterations = 1000
    start = time.time()
    for i in range(iterations):
        eax = itp.threads[0].state.regs.eax
        ebx = itp.threads[0].state.regs.ebx
    print("Individual state reads took %s seconds to complete %d iterations"%(time.time()-start, iterations))
    setup()
    runJobMultipleStateRead('HSX0_C0_T0', iterations)
    #goall()
except BaseException, e:
    traceback.print_exc()
    

