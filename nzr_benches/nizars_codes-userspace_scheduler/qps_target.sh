y=1
var=1
oldset=0
setcpushare=1024
cpu_qouta_low_priority=50000000
period=1000000
qps_old=0
qps_target=800
./kill.sh
rm -f outfile
echo "killed all previous instances"
echo "killing all"
echo "create a cgroup and set default cpu share limit and cpu time limit for cgroups"
cgcreate -g cpu:/cpulimited
cgcreate -g cpu:/lesscpulimited
cgset -r cpu.shares=512 cpulimited
cgset -r cpu.shares=1024 lesscpulimited
cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
cgset -r cpu.cfs_period_us=$period cpulimited
cgset -r cpu.cfs_quota_us=-1 lesscpulimited
cgset -r cpu.cfs_period_us=$period lesscpulimited

cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main
cgexec -g cpu:lesscpulimited /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/./B_new_script.sh >/root/scheduler/outfile800 &

sleep 30

cd /root/test_cpp/rdpmc_test
cgexec -g cpu:cpulimited ./cpu_stress &
pid=$(echo $!)
cd /root/scheduler/
#echo "sleep before launching benchmark"
for((i=0;i<300;i++ ))
	do
	#set=$((perf stat -e cycles,instructions -a sleep 5 ) |& egrep -o " [0-9]{0,3}.[0-9]{2} " )
	#echo "The current IPC is $set"
	#var2=$(echo "100*$set - 100*$oldset" | bc -l)
	#oldset=$set
	#var3=$(echo "$setcpushare +  $var2 "| bc)
	#echo " the differnece is $var2"
	#setcpushare=${var3%.*}
	#time_quota=$(echo "$cpu_qouta_low_priority +100000*$var2 " | bc )
	#cpu_qouta_low_priority=${time_quota%.*}
	#test_condition=$((2+ cpu_qouta_low_priority/period))
	#cpu_usage=$(cat <(grep 'cpu ' /proc/stat) <(sleep 1 && grep 'cpu ' /proc/stat) | awk -v RS="" '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}')
	#cpu_usage=${cpu_usage%.*}
	sleep 3
	#cgset -r cpu.shares=$setcpushare lesscpulimited
	#cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
	temp=$(head -n 1 /sys/fs/cgroup/cpu/lesscpulimited/tasks)
	qps=$(tail -n 1 outfile800 | egrep -o "^[0-9]{1,7}\.{0,1}[0-9]{1,7}" )
	qps_diff=$(echo " -0.01*$period*$qps_target +0.01*$period*$qps " | bc )
	qps_old=$qps
	qps_scaling=${qps_diff%.*}
	time_quota=$(echo "$cpu_qouta_low_priority +$qps_scaling " | bc )
        cpu_qouta_low_priority=${time_quota%.*}
        test_condition=$((2+ cpu_qouta_low_priority/period))
	coreTime=$(echo "$cpu_qouta_low_priority*0.000001" |  bc)
	echo "the diffrence in qps is: $qps_scaling and the allowed  core usage is $coreTime cores "
	cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
	if [ $temp -gt 0 ]
		then
		cgset -r cpu.shares=$setcpushare lesscpulimited
		cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
		else
		cgset -r cpu.cfs_quota_us=112000000 cpulimited
	fi
	#echo " The current IPC is $set  the differnece is $var2 ,  the new cpu share is  $setcpushare and qouta is $cpu_qouta_low_priority cpu_usage is $cpu_usage"
        
done

