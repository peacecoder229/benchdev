current=$(pwd)
pid1=0
cd /root/test_cpp/rdpmc_test
./cpu_stress 56 &
pid1=$(echo $!)
sleep 1
./cpu_stress 56 &
pid2=$(echo $!)
echo " pid 1 is $pid1 and pid2 is $pid2"
cd $current
#perf stat -e CPU_CLK_UNHALTED.REF_TSC,tsc -p $pid2 -I 1000 -o perf_out &
perf stat -e CPU_CLK_UNHALTED.REF_TSC,tsc -p $pid2 -I 1000 -o perf_out &
tests=$(echo $!)
echo " PID is $tests"

for ((i=0 ; i< 50; i++))
do
	sleep 1
	clock=$(tail -n 1 perf_out | awk ' { print $2  } ' )
	used=$(tail -n 2 perf_out | awk ' { print $2  } ' | head -1 )
	clck=$(echo $clock | sed 's/[^0-9]*//g')
	clck_used=$(echo $used | sed 's/[^0-9]*//g')
	utlz=$(echo "scale = 6; 100* $clck_used / $clck " | bc)
	echo "$clck and $clck_used and cpu utilization is: $utlz "
	#a=$( head -1 $files  )
	#b=$( head 1 $files )
	#echo "the res are $a and $b "
done

kill $tests

