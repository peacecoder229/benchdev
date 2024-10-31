import workload_client
import monitor.monitor_client


user_workload_client = workload_client.WorkloadClient('127.0.0.1', '2035')
user_monitor_client = monitor.monitor_client.MonitorClient('127.0.0.1', '2036')

# add PR workload to workload_scheduler_stub
user_workload_client.add_workload("specjbb2015", "PR")

# define how to monitor performance
user_monitor_client.set_latency_target((6000,8000), "specjbb2015")

# add BE workload to workload_scheduler_stub
for i in range(14):
    user_workload_client.add_workload("stream", "BE")
