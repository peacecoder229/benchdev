y=1
var=1
oldset=0
setcpushare=1024
cpu_qouta_low_priority=56000000
period=1000000
./kill.sh
echo "killed all previous instances"
echo "killing all"
echo "create a cgroup and set default cpu share limit and cpu time limit for cgroups"
cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main

# 1 ms granularity
echo 1000000 > /proc/sys/kernel/sched_min_granularity_ns

/pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh  > /root/scheduler/output_11ms

echo "finished task"
cd /root/test_cpp/rdpmc_test
./kill.sh



cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main
#crity
echo 1000000 > /proc/sys/kernel/sched_min_granularity_ns

/pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh  > /root/scheduler/output_12ms

echo "finished task"
cd /root/test_cpp/rdpmc_test
./kill.sh 
#./cpu_stress & 

cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main
#crity
echo 1000000 > /proc/sys/kernel/sched_min_granularity_ns

/pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh  > /root/scheduler/output_13ms

echo "finished task"
cd /root/test_cpp/rdpmc_test
./kill.sh
#./cpu_stress &


echo "sleep before launching benchmark"

