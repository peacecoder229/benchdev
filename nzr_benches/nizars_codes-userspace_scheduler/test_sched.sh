y=1
var=1
oldset=0
setcpushare=1024
cpu_qouta_low_priority=40000000
period=1000000
./kill.sh
get_pwd=$(pwd)
echo "killed all previous instances"
echo "killing all"
echo "create a cgroup and set default cpu share limit and cpu time limit for cgroups"
cgcreate -g cpu:/cpulimited
cgcreate -g cpu:/lesscpulimited
cgreate -g cpu,perf_events:/HPjob
cgset -r cpu.shares=256 cpulimited
cgset -r cpu.shares=1024 lesscpulimited
cgset -r cpu.shares=2048 HPjob
cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
cgset -r cpu.cfs_period_us=$period cpulimited
cgset -r cpu.cfs_quota_us=-1 lesscpulimited
cgset -r cpu.cfs_period_us=$period lesscpulimited
cgset -r cpu.cfs_quota_us=-1 HPjob
cgset -r cpu.cfs_period_us=$period HPjob

# launch search workload as an HPjob
cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main
cgexec -g cpu:HPjob /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh > /root/scheduler/out/test_out 
pid2=$(echo $!)
echo " search PID is $pid2"
#indicate which perf_events task belong tothis cgroup
echo $pid2 > /sys/fs/cgroup/perf_event/HPjob/tasks
echo "sleep before launching benchmark"
sleep 30

cd /root/test_cpp/rdpmc_test
cgexec -g cpu:cpulimited ./cpu_stress &
pid=$(echo $!)

cd $get_pwd
#(perf stat -e cycles,instructions -G HPjob -I 5000 ) |& egrep -o " [0-9]{0,3}.[0-9]{2} " > perf_out
perf stat -e cycles,instructions -G HPjob -I 5000 -o perf_out &
perf_pid=$(echo $!)
echo "the perf pid is $perf_pid"
for((i=0;i<300;i++ ))
	do
	#set=$((perf stat -e cycles,instructions -G HPjob ) |& egrep -o " [0-9]{0,3}.[0-9]{2} " )
	sleep 5
	set=$(tail -n 2 perf_out |  egrep -o " [0-9]{0,3}.[0-9]{1,2} "  )
	echo "The current IPC is $set"
	var2=$(echo "10*$set - 10*$oldset" | bc -l)
	oldset=$set
	var3=$(echo "$setcpushare +  $var2 "| bc)
	#echo " the differnece is $var2"
	setcpushare=${var3%.*}
	time_quota=$(echo "$cpu_qouta_low_priority +100000*$var2 " | bc )
	cpu_qouta_low_priority=${time_quota%.*}
	test_condition=$((2+ cpu_qouta_low_priority/period))
	#cpu_usage=$(cat <(grep 'cpu ' /proc/stat) <(sleep 1 && grep 'cpu ' /proc/stat) | awk -v RS="" '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}')
	#cpu_usage=${cpu_usage%.*}
	cgset -r cpu.shares=$setcpushare HPjob
	cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
	temp=$(head -n 1 /sys/fs/cgroup/cpu/HPjob/tasks)

	if [ $temp -gt 0 ]
		then
		cgset -r cpu.shares=$setcpushare HPjob
		cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
		else
		cgset -r cpu.cfs_quota_us=112000000 cpulimited
	fi
	#echo " The current IPC is $set  the differnece is $var2 ,  the new cpu share is  $setcpushare and qouta is $cpu_qouta_low_priority cpu_usage is $cpu_usage"

done

kill $perf_pid
