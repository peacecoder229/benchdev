# 1. Introduction:

This repo contains code for userspace scheduler using Cgroups and perf event

This scheduler is manages allow the user to divide the CPU time between two group of jobs, high priority and low priority

this DOES NOT replace the Linux scheduler based on completly fair scheduler, rahter it uses the built it in controls to dynamicaly control how much CPU is allowed

Cgroups in linux has built in monitors and scheudling tools. For scheduling we care most about two set of controls, CPU shares, and CPU time and period.

There are four different example scripts here, two controls based on CPU utilization and two based on custom performance metric from binary :

## All binaries in the scripts are hardcoded, so if you want to copy this on your machine you will need to change the location of your biniary

# 2. how the userspace scheudler work and what are the important varaible within the scripts

this script contains the a dynamic scheduler based on CPU utlization. The script will launch high priority job and low priority job and create  a corresponding cgroup.

The Cgroup of high priority get a bigger cpu.share than the other low priority share. The cpu.share is a soft limit meaning that if we give 75% to high priority and 25% to low priority , the high prioirty can use upto 75% if low priority is runnig or more if the low prioirty is not running or not using its share, and vice versa.

However since modern CPU have hyper-threading and share resoruces inside the core and caches, cpu.shares is not enought metric to devide the cpu time. Thus we have to use a more involved method using scheduling period and time. also know as quota.

cpu.cfs_period_us sets the schedulign period in us, the scheduler will that time period as a reference for 1 CPU.
cpu.cpu.cfs_quota_us: set the quota of the task .

	nb of equivalent cores =cpu.cfs_quota_us/cpu.cfs_period_us 

for example if   cpu.cfs_quota_us = 10,000,000  and    cpu.cfs_period_us= 1,000,000 then the ratio 10

this means that the cputime that can be used for this task is equivalent to 10 cpu  (this can be 10 core all the time or 100 cores 10% of the time, or 50 cores 20% of the time ...). This will work with other control like numactl or cpuset. 

In all our scripts we use the cpu.share on boht high priority and low priority task, but we ues the period and quota for a hard limit on the low priority but not high priority.

In the linux scheduler, each PID will keep the track on how much time is spent running. Al threads in the cgroup will borrow time fro their parents, decreasing the availalbe quoota, once hte quota is exhausted, the threads withinthe cgroup will be removed form the scheduler runqueue. Once the period has been exhausted the quota is refreshed for the cgroup and the task will be reinsered in the runqueue.
 
3. different scripts

In this repo there are 4 differnt scripts that manages that cou resources.

dyanmic_cpu.sh uses perf event to measure changes in cpu utilization over time, if utilization drop it means that the HP task might suffer so throttle the low priority harder. In case the cpu utilization is increasing, it means that low priority is being throttled too much and then we allow to it to run more time. This way we can keep the performance steady

target_cpu.sh: this allow us to target a specific Cpu utlization. If the cpu utlization of high priority task exceed the target we can increae the quota of the low priority, if the utilization of the high priority dropped below the target we throttle the low priority to allow the high priority task to use more cpu time

qps_target.sh : uses a custom target that read direcly form HP task (in our exmaple query per second) that output is saved to file and our scheduler read it once second (or few secods). the period of low priority task is adjusted bsed on the differnce between the target QPS and measured QPS

qps_dynamic.sh: read QPS and adjust low priority quota based whether the QPS is dropping or increasing.

the cpu.util.sh scripts uses perf_event to measure cpu utlization, if we notice the utilzation of the high priority task dropping indicates that the we are using less high priority task, so we 

There are two ways to do that, to set a perfomance target and control CPU time to acheive that target.

or measure differne in CPU utilization and use that differece to allow more or less CPU tasks for a cgroup

perf event is used to measure utilziaiton and Cgroup is used to meausre CPU time and control allowed time

Note:
Most of these codes are hard coded and might not work as is on other machines.

perf event is part of linux common tool and needed to run these scripts

The QPS based CPU scheduler needs to reed custum performance meteric from the running app, the easiest way is to write to file and use linux shell to read latest input and adjust time share based on read metric.  while the cpu utilization based resource management is more program agnostic but cannot garantee specific throughtput like hte QPS apporch.

