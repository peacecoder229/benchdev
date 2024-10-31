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
/pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./C_new_scipt.sh > /root/scheduler/outfile_no_sched2 &
sleep 30
cd /root/test_cpp/rdpmc_test
taskset -c 28-55,84-111 ./cpu_stress & 
echo "sleep before launching benchmark"

