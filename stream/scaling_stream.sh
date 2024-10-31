#!/bin/bash


source test.src.sh
source test_process.src.sh

cd /pnpdata/hwpdesire
/pnpdata/hwpdesire/hwpdesire.sh -r
/pnpdata/hwpdesire/hwpdesire.sh -m 2700000
/pnpdata/hwpdesire/hwpdesire.sh -a 2700000

cd - 
	
function emon_monitor(){

	path=$1
	
	emon -v > $path/emon-v.dat
	emon -M > $path/emon-m.dat

	emon_conf="conf/emon/skx.conf"
	taskset -c 28 emon -i $emon_conf > $path/emon.dat &
	
}

function workload(){
	result_path=$1
	ir=$2

	prepare
	heap="30"

	set_llc_mba $HP_WAY $HP_WAY $HP_MBA $HP_MBA	
	mkdir -p $result_path

	taskset -c 28 pqos -r  -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &

	emon_monitor $result_path

	for i in `seq 5`
	do
		./stream_omp > $result_path/score_src.txt
	done

	emon -stop
	tail -7 $result_path/score_src.txt | head -4 > $result_path/score.txt
	pkill -9 pqos
}

for core in `seq 1 17`
do			
		HP_CPUSET=0-$core
		HP_WAY=11
		HP_MBA=100
		export OMP_NUM_THREADS=$(( $core + 1 ))
		WORK_PATH="core_${core}"
		
		LP_CPUSET=$HP_CPUSET

		workload $WORK_PATH $ir
done
exit
for HP_WAY in `seq 1 11`
do
		HP_CPUSET=0-35
		HP_MBA=100

		LP_CPUSET=$HP_CPUSET

		WORK_PATH="cat_${HP_WAY}"

		workload $WORK_PATH $ir
done

MBA="10
20 
30 
40 
50 
90 
"

for HP_MBA in $MBA
do
		HP_CPUSET=0-35
		HP_WAY=11
		
		LP_CPUSET=$HP_CPUSET

		WORK_PATH="mba_${HP_MBA}"
		workload $WORK_PATH $ir

done

for ir in `seq 10 2 25`
do
		
		HP_CPUSET=0-35
		HP_WAY=11
		HP_MBA=100
		ir=${ir}000

		WORK_PATH="ir_${ir}"
		workload $WORK_PATH $ir
done


ir=10000
for i in `seq 10 25`
do
		~/hwpdesire/hwpdesire.sh -m ${i}00000
	        ~/hwpdesire/hwpdesire.sh -a ${i}00000
		

		HP_CPUSET=0-35
		HP_WAY=11
		HP_MBA=100

		WORK_PATH="freq_${i}"
		workload $WORK_PATH $ir

done
