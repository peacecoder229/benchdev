y=1
var=1
oldset=0
setcpushare=1024
cpu_qouta_low_priority=50000000
period=1000000
./kill.sh  #kill previous runs
get_pwd=$(pwd)
s_to_ms=1000
sleep_period=5
target_util=30
echo "killed all previous instances"
echo "killing all"
echo "create a cgroup and set default cpu share limit and cpu time limit for cgroups"
cgcreate -g cpu:/cpulimited
cgcreate -g cpu:/lesscpulimited
cgcreate -g cpu,perf_events:/HPjob
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
cgexec -g cpu:HPjob /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh > /root/scheduler/out/test_out & 
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
#get the the number of clocks where the cpu was busy every few seconds
perf stat -e  CPU_CLK_UNHALTED.REF_TSC -G HPjob -I $((sleep_period*s_to_ms)) -o perf_out &
perf_pid=$(echo $!)
echo "the perf pid is $perf_pid"
for((i=0;i<300;i++ ))
	do
	# get the total number of cpu clcks
	clk=$( perf stat -a -e tsc sleep $sleep_period  |& egrep -o " ([0-9]{1,3},){0,7}[0-9]{3} " )
	# read the number of clock utilization
	util=$(tail -n 1 perf_out | awk ' { print $2  } '  )
	clck=$(echo $clk | sed 's/[^0-9]*//g')
        clck_used=$(echo $util | sed 's/[^0-9]*//g')
	#get task cpu utilization 
	utlz=$(echo "scale = 6; 100* $clck_used / $clck " | bc)
        echo "search cpu utilization is: $utlz "
	set=${utlz%.*}
	#check differnece of utilizaiton
	var2=$(echo "  $set - $target_util" | bc -l)
	#oldset=$set
	#var3=$(echo "$setcpushare +  $var2 "| bc)
	#echo " the differnece in cpu.share is $var2"
	#setcpushare=${var3%.*}
	time_quota=$(echo "$cpu_qouta_low_priority -100000*$var2 " | bc )
	core_equivalent=$(echo "scale = 10 ; $time_quota/1000000" | bc )
	echo " the number of cores equivalent $core_equivalent amd time quota is $time_quota"
	cpu_qouta_low_priority=${time_quota%.*}
	test_condition=$((2+ cpu_qouta_low_priority/period))
	#cpu_usage=$(cat <(grep 'cpu ' /proc/stat) <(sleep 1 && grep 'cpu ' /proc/stat) | awk -v RS="" '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}')
	#cpu_usage=${cpu_usage%.*}
	cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
	temp=$(head -n 1 /sys/fs/cgroup/cpu/HPjob/tasks)
	temp2=${utlz%.*}
	if [ $temp -gt 0 ]
		then
		cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
		else
		cgset -r cpu.cfs_quota_us=112000000 cpulimited
	fi
	#echo " The current IPC is $set  the differnece is $var2 ,  the new cpu share is  $setcpushare and qouta is $cpu_qouta_low_priority cpu_usage is $cpu_usage"

	done

kill $perf_pid
