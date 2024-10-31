import workload_client
import monitor.monitor_client


user_workload_client = workload_client.WorkloadClient('127.0.0.1', '2035')
user_monitor_client = monitor.monitor_client.MonitorClient('127.0.0.1', '2036')

# add PR workload to workload_scheduler_stub
for i in range(1):
    user_workload_client.add_workload("redis", "PR")

# define how to monitor performance
user_monitor_client.set_qps_target((140000,145000), "redis")

# add BE workload to workload_scheduler_stub
for i in range(28):
    user_workload_client.add_workload("stream", "BE")
