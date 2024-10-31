y=1
var=1
oldset=0
setcpushare=1024
cpu_qouta_low_priority=10000000
period=1000000
./kill.sh  #kill previous runs
get_pwd=$(pwd)
s_to_ms=1000
sleep_period=5
echo "killed all previous instances"
echo "killing all"
echo "create a cgroup and set default cpu share limit and cpu time limit for cgroups"

#yum install libcgroup-tools.x86_64

cgcreate -g cpu:/cpulimited
cgcreate -g cpu,perf_events:/HPjob
cgset -r cpu.shares=256 cpulimited
cgset -r cpu.shares=2048 HPjob
cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
cgset -r cpu.cfs_period_us=$period cpulimited
cgset -r cpu.cfs_quota_us=-1 HPjob
cgset -r cpu.cfs_period_us=$period HPjob

# launch search workload as an HPjob
# cgexec -g cpu:HPjob docker run -it tf_rn50_nizar:latest  & 

docker run --cpu-shares 2048 -t tf_rn50_nizar:latest  &

pid2=$(echo $!)
echo " search PID is $pid2"
#indicate which perf_events task belong tothis cgroup
echo $pid2 > /sys/fs/cgroup/perf_event/HPjob/tasks
echo "sleep before launching benchmark"
sleep 10

cgexec -g cpu:cpulimited ./512_cpu_stress_avx &
pid=$(echo $!)

#(perf stat -e cycles,instructions -G HPjob -I 5000 ) |& egrep -o " [0-9]{0,3}.[0-9]{2} " > perf_out
#get the the number of clocks where the cpu was busy every few seconds

container_name=$(docker ps | awk '{print $NF}'| tail -n 1)

echo "the container name is: $container_name"

perf stat -e  CPU_CLK_UNHALTED.REF_TSC -p $pid2 -I $((sleep_period*s_to_ms)) -o perf_out &
perf_pid=$(echo $!)
echo "the perf pid is $perf_pid"
for((i=0;i<300;i++ ))
	do
	# get the total number of cpu clcks
	clk=$( perf stat -a -e tsc sleep $sleep_period |& grep tsc | awk '{print $1}' | sed 's/,//g' )
	# read the number of clock utilization
	util=$(tail -n 1 perf_out | awk '{print $2}' )
    clck=${clk}
    clck_used=$( echo $util | sed 's/,//g' )
	echo "clck is $clck and clck_used $clck_used and clock is $clk while util is $util "
    #get task cpu utilization 
    utlz=$( echo "scale = 7; 100* $clck_used / $clk " | bc )
    echo "search cpu utilization is: $utlz "
    set=${utlz+1}
	#check differnece of utilizaiton
    echo "  $set - $oldset"
    var2=$( echo "  $set - $oldset" | bc -l )
    oldset=${set}
	
    echo " the differnece in cpu.share is $var2"
	time_quota=$(echo "$cpu_qouta_low_priority +100000*$var2 " | bc )
	core_equivalent=$(echo "scale = 10 ; $time_quota/1000000" | bc )
	echo " the number of cores equivalent $core_equivalent amd time quota is $time_quota"
	cpu_qouta_low_priority=${time_quota%.*}
	test_condition=$((2+ cpu_qouta_low_priority/period))
	#cpu_usage=$(cat <(grep 'cpu ' /proc/stat) <(sleep 1 && grep 'cpu ' /proc/stat) | awk -v RS="" '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5)}')
	#cpu_usage=${cpu_usage%.*}
	cgset -r cpu.cfs_quota_us=$cpu_qouta_low_priority cpulimited
	#echo " The current IPC is $set  the differnece is $var2 ,  the new cpu share is  $setcpushare and qouta is $cpu_qouta_low_priority cpu_usage is $cpu_usage"

	done

kill $perf_pid
