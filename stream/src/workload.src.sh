	
function prepare(){
	# Please make sure to run it before test
	#
	mkdir -p $WORK_PATH

	lscpu | unix2dos > $WORK_PATH/cpuinfo.txt
	free | unix2dos > $WORK_PATH/meminfo.txt
	uname -a >> $WORK_PATH/kernel.txt

	pqos -R
	
	for docker_id in `docker ps -a | grep -v CONTAINER | awk '{print $1}' `
	do
		docker rm -f $docker_id
	done
	
	echo "Platform: ${PLAFORM}" >> $WORK_PATH/cmd.txt
	
	echo "Instance(h/l): ${HP_INSTANCES} / ${LP_INSTANCES} / ${AEP_INSRANCES}" >> $WORK_PATH/cmd.txt
	echo "CPUSET(h/l):  ${HP_CPUSET} / ${LP_CPUSET} / ${AEP_CPUSET}" >> $WORK_PATH/cmd.txt
	echo "LLC(h/l): ${HP_WAY} / ${LP_WAY} / ${AEP_WAY}" >> $WORK_PATH/cmd.txt
	echo "MBA (h/l): ${HP_MBA} /  ${LP_MBA} / ${AEP_MBA}" >> $WORK_PATH/cmd.txt

}

function teardown(){
	# call it after test finished

	sleep 0
}

function specjbb_2005_aep(){
	# Need AEP + customized JVM
	# $1 warehouse setting

    wh=$1
    duration=180000
    opt="-XX:HeapDir=/dev/dax12.0"

    result_path="$WORK_PATH/LP-specjbb_2005_aep"
    mkdir -p $result_path

    echo "==start test specjbb_2005_aep WH:${wh}=="
    docker run --name LP-specjbb_2005_aep-${wh}wh --rm --cpuset-cpus=$LP_CPUSET \
                  --device=/dev/dax12.0:/dev/dax12.0 -v `pwd`/$result_path:/results -e WAREHOUSE=$wh \
                  -e DURATION=${duration} -e JAVA_OPTS_AEP="${opt}" specjbb_2005_ali:1.8

}

function start_specjbb2015(){
	# $1 IR setting for 2015

	ir=$1
	duration=180000

	opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

	result_path="$WORK_PATH/HP_specjbb2015_IR${ir}"
	mkdir -p $result_path

	echo "==start test specjbb2015 IR:${ir} (HP)=="
	docker run --name HP-specjbb2015-IR${ir} --rm -v `pwd`/$result_path:/result -e CONF_IR="${ir}" -e CONF_DURATION=${duration} -e JAVA_OPTS="${opt}" --cpuset-cpus=$HP_CPUSET specjbb2015:quick

	# cp $result_path/result/*/specjbb2015-*/*/data/rt-curve/specjbb2015*overall-throughput-rt.txt $WORK_PATH/score.txt
	# summary results
	input_file=`find ${result_path} -name "*overall-throughput-rt.txt"`
	python utility/specjbb2015_score.py ${input_file} > $WORK_PATH/score.txt

	#time_perf_file=`find ${result_path} -name "*getPerfTimeDelayFiltered.txt"`
	#cp ${time_perf_file} $WORK_PATH/jbb2015_time_perf.txt
	
	# this fixed a problem: filename too long to copy correctly in windows OS
	#for pack in `ls ${result_path}`
	#do
	#	tar cfj $result_path/${pack}.tar.bz2 $result_path/${pack}
	#	rm -rf  $result_path/${pack}
	#done
}

function start_specjbb2015_lp(){
    # $1 IR setting

	ir=$1
	opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

	result_path="$WORK_PATH/LP_specjbb2015_IR${ir}"
	mkdir -p $result_path

	echo "==start test specjbb2015 IR:${ir} (LP)=="
	while [ 1 = 1 ]
	do
	    docker run --name LP-specjbb2015-IR${ir} --rm -v `pwd`/$result_path:/result -e CONF_IR="${ir}" -e JAVA_OPTS="${opt}" --cpuset-cpus=$LP_CPUSET specjbb2015:quick
	done
}


function start_specjbb(){
    # $1 specjbb warehouse setting

	wh=$1
	#opt="-server -showversion -Xmx29g -Xms29g -Xmn27g -XX:ParallelGCThreads=${wh} -XX:+UseLargePages -XX:+UseParallelOldGC -XX:-UseSuperWord"
	opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log -XX:ParallelGCThreads=${wh}"

	result_path="$WORK_PATH/HP_specjbb_wh${wh}"
	mkdir -p $result_path

	echo "==start test specjbb WH:${wh}(HP)=="
	docker run --name HP-specjbb-${wh}wh --rm -v `pwd`/$result_path:/results -e WAREHOUSE=$wh \
	           -e JAVA_OPTS="${opt}" --cpuset-cpus=$HP_CPUSET specjbb:quick

	awk '{print "HP:specjbb2005:wh"$4 "," $6 }' $result_path/summary.txt >> $WORK_PATH/score.txt
}


function start_specjbb_lp(){
    # $1 specjbb warehouse

	wh=$1
	#opt="-server -showversion -Xmx29g -Xms29g -Xmn27g -XX:ParallelGCThreads=${wh} -XX:+UseLargePages -XX:+UseParallelOldGC -XX:-UseSuperWord"
	opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log -XX:ParallelGCThreads=${wh}"

	result_path="$WORK_PATH/LP_specjbb_wh${wh}"
	mkdir -p $result_path

	echo "==start test specjbb WH:${wh}(LP)=="
	docker run --name LP-specjbb-${wh}wh --rm -v `pwd`/$result_path:/results -e WAREHOUSE=$wh -e JAVA_OPTS="${opt}" --cpuset-cpus=$LP_CPUSET specjbb:quick
	awk '{print "LP:specjbb2005:wh"$4 "," $6 }' $result_path/summary.txt >> $WORK_PATH/score.txt
}

# Stream must be a LP workloads
function start_stream() {
	# $1 stream quantity

	count=$1
	echo "==Start $count streams=="
	for i in `seq 1 $count`
	do
		docker run --cpuset-cpus=$LP_CPUSET -d --name LP-stream-$i stream
	done

}

function stop_workload(){
	# $1 container name

	docker ps -a | grep $1 | awk '{print $1}' | xargs docker rm -f
}

function wait_docker_stop(){
	# $1 container name

	running=1
	while [ $running -gt 0 ]
	do
		sleep 1
		running=`docker ps | grep $1 | wc -l`

	done
}

function start_mlc() {
	# unsafe, use is carefully

	echo "==Start $count mlc=="
	mlc --loaded_latency -d0 -t1000 -k$LP_CPUSET
}

function stop_mlc(){

	killall -9 mlc
}

function start_speccpu(){
	# $1 workload type
	# $2 running copies

	result_path="$WORK_PATH/speccpu/$1_result"
	mkdir -p $result_path

	echo "==start SPECcpu $1=="
	#docker run --name speccpu-$1 --rm -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=$2 -e WORKLOAD=$1 --cpuset-cpus=$LP_CPUSET speccpu2006
	docker run --name HP-speccpu-$1 --rm -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=$2 -e WORKLOAD=$1 --cpuset-cpus=$LP_CPUSET speccpu2006:deadloop

	score=`grep mcf $result_path/*.ref.txt  | head -2 | tail -1 | awk '{print $3","$4}'`
	echo $1","$score >>  $WORK_PATH/score.txt
}

function start_speccpu_combo_hp(){
	# Run each of specjbb cases in parallel
	#
	# $1 workloads quantity

	wl=$1
	# read workload list from conf file
	workloadlist=(`cat conf/SPECcpu2006/CINT | sort -R `)

	count=`cat conf/SPECcpu2006/CINT | wc -l `

	for i in `seq 0 $((${wl}-1))`
	do
		workload=${workloadlist[$(($i%$count))]}

		result_path="$WORK_PATH/hp_speccpu_combo_results/${i}.${workload}"
		mkdir -p $result_path

		echo "== start SPECcpu ${i}.${workload}(HP) =="
		docker run --name HP-speccpu-${i}.${workload} -d -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=1 -e WORKLOAD=$workload --cpuset-cpus=$HP_CPUSET speccpu2006:deadloop &
	done

	# each of the workload will generate a *001.ref.txt when benchmark finished.
	# count those files and validate if all workloads finished
	finished=0
	while [ $finished -lt $wl ]
	do
		sleep 10
		finished=`find ${WORK_PATH}/hp_speccpu_combo_results -name "*001.ref.txt"  | wc -l`

	done

	stop_workload HP-speccpu

	# summary the results
	for result_path in `ls $WORK_PATH/hp_speccpu_combo_results`
	do
		name=${result_path##*.}
	#	name=${name##*.}
		score=`grep ${name} $WORK_PATH/hp_speccpu_combo_results/${result_path}/*.ref.txt  | head -2 | tail -1 | awk '{print $3","$4}'`
		echo $name","$score >>  $WORK_PATH/score.txt
	done

}

function start_speccpu_combo(){
	# $1 workloads quantity

	wl=$1
	workloadlist=(` cat conf/SPECcpu2006/CINT | sort -R `)
	count=`cat conf/SPECcpu2006/CINT | wc -l `

	for i in `seq 0 $((${wl}-1))`
	do
		workload=${workloadlist[$(($i%$count))]}

		result_path="$WORK_PATH/lp_speccpu_combo_results/${i}.${workload}"
		mkdir -p $result_path

		echo "== start SPECcpu ${i}.$workload(LP) =="
		docker run --name LP-speccpu-${i}.${workload} -d -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=1 -e WORKLOAD=$workload --cpuset-cpus=$LP_CPUSET speccpu2006:deadloop &
	done

}

function start_specjbb2015_dynamic(){
	# this workload has a trigger to run scripts for each test iterations
	#
	# $1 specjbb IR setting

	ir=$1
	duation=80000
	opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

	result_path="$WORK_PATH/HP_specjbb2015_IR${ir}"
	mkdir -p $result_path

	echo "==start to test dynamic specjbb2015 IR:${ir} (HP)=="
	docker run --name HP-specjbb2015-IR${ir} --rm -v `pwd`/$result_path:/result -e CONF_IR="${ir}" \
	         -e CONF_DURATION=${duation} -e JAVA_OPTS="${opt}" --cpuset-cpus=$HP_CPUSET specjbb2015:quick &

	pid=$!
	# waitting for output file generated.
	sleep 7
	outputs=`find $result_path -name 'composite.out' | tail -1 `

	# feed file changes to python script
	python utility/dynamic_config.py -p specjbb2015 -w "tail -s 0.3 -f $outputs" -f task.json >> $WORK_PATH/results.txt &
	# wait for docker container finished
	wait $pid
}
function start_specjbb2015_multi(){
	# $1 IR setting for 2015

	ir=$1
#time in mS
	duration=80000
        yongGC=`echo "$2 * 9 / 10" | bc -l | cut -f1 -d"."`

	opt="-Xmx${2}g -Xms${2}g -Xmn${yongGC}g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

	result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${HP_INSTANCES}_HEAP${heap}"
	mkdir -p $result_path

	echo "==start test specjbb2015 IR:${ir} (HP)=="
	docker run --name HP-specjbb2015multi-IR${ir}Heap${2} --rm -v `pwd`/$result_path:/result -e CONF_IR="${ir}" -e CONF_DURATION=${duration} -e NUM_OF_RUNS=1 -e JAVA_OPTS="${opt}" --cpuset-cpus=$HP_CPUSET specjbb2015:multi

	# cp $result_path/result/*/specjbb2015-*/*/data/rt-curve/specjbb2015*overall-throughput-rt.txt $WORK_PATH/score.txt
	# summary results
#	input_file=`find ${result_path} -name "*overall-throughput-rt.txt"`
#	python utility/specjbb2015_score.py ${input_file} > $WORK_PATH/score.txt

	#time_perf_file=`find ${result_path} -name "*getPerfTimeDelayFiltered.txt"`
	#cp ${time_perf_file} $WORK_PATH/jbb2015_time_perf.txt
	
	# this fixed a problem: filename too long to copy correctly in windows OS
	#for pack in `ls ${result_path}`
	#do
	#	tar cfj $result_path/${pack}.tar.bz2 $result_path/${pack}
	#	rm -rf  $result_path/${pack}
	#done
}
function many_specjbb2015_multi(){
	# $1 IR setting for 2015

	ir=$1
#time in mS
	duration=1800000
        yongGC=`echo "$2 * 9 / 10" | bc -l | cut -f1 -d"."`
        perm=`echo "$2 * 7 / 10" | bc -l | cut -f1 -d"."`

	opt="-Xmx${2}g -Xms${2}g -Xmn${yongGC}g -XX:PermSize${perm}g -XX:+UseG1GC -XX:ParallelGCThreads=${HP_INSTANCES} -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

	#result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${HP_INSTANCES}_HEAP${heap}"
	mkdir -p $result_path
        cpu=$3
        cpumod="${cpu//,/-}"
	echo "==start test specjbb2015 IR:${ir} (HP)== cpu is ${cpu} and CPUMOD is ${cpumod}"
	docker run --name HP-specjbb2015multi-IR${ir}Heap${2}core${cpumod} --rm -v `pwd`/$result_path:/result -e CONF_IR="${ir}" -e CONF_DURATION=${duration} -e NUM_OF_RUNS=1 -e JAVA_OPTS="${opt}" --cpuset-cpus=$HP_CPUSET specjbb2015:multi

	# cp $result_path/result/*/specjbb2015-*/*/data/rt-curve/specjbb2015*overall-throughput-rt.txt $WORK_PATH/score.txt
	# summary results
#	input_file=`find ${result_path} -name "*overall-throughput-rt.txt"`
#	python utility/specjbb2015_score.py ${input_file} > $WORK_PATH/score.txt

	#time_perf_file=`find ${result_path} -name "*getPerfTimeDelayFiltered.txt"`
	#cp ${time_perf_file} $WORK_PATH/jbb2015_time_perf.txt
	
	# this fixed a problem: filename too long to copy correctly in windows OS
	#for pack in `ls ${result_path}`
	#do
	#	tar cfj $result_path/${pack}.tar.bz2 $result_path/${pack}
	#	rm -rf  $result_path/${pack}
	#done
}
