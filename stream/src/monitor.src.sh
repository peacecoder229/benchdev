#cores to run monitors
MONITOR_CORE=28

function start_pqos_monitor(){
	# monitor by CMT/MBM 

	taskset -c ${MONITOR_CORE} pqos -r -i 5 -m "all:[$LP_CPUSET],[$HP_CPUSET],[$AEP_CPUSET]"  -o $WORK_PATH/rdt.out &
}

function stop_pqos_monitor(){
	pkill -9 pqos

	# convert output file to execel
    #python pqos2excel.py $WORK_PATH/rdt.out $WORK_PATH/${HP_INSTANCES}-${STREAM_COUNT}_C${HP_CPUSET}-${LP_CPUSET}_L${HP_WAY}
    #python utility/pqos2excel.py $WORK_PATH/rdt.out $WORK_PATH/`date +%H%M%S`
}

function start_emon(){
	# var SEP_LOC_PATH  was defind by sep_var.sh. this value is depended by emon.

	if [ $SEP_LOC_PATH ] 
	then
	#	$SEP_LOC_PATH/sepdk/src/rmmod-sep
	#	$SEP_LOC_PATH/sepdk/src/insmod-sep

		emon_conf="conf/emon/skx.conf"
 		if [ $PLAFORM = "bdw" ]
 		then
 			emon_conf="conf/emon/bdw.conf"
 		fi

  		emon -v   > $WORK_PATH/emon-v.dat
 		emon -M   > $WORK_PATH/emon-m.dat

 		taskset -c ${MONITOR_CORE} emon -i $emon_conf > $WORK_PATH/emon.dat &

	fi

}

function stop_emon(){
	if [ $SEP_LOC_PATH ]
	then
	  emon -stop
	  # bzip2 $WORK_PATH/emon.dat
	fi

}

function start_lwm(){
	cd utility/lightweight_monitor
	taskset -c ${MONITOR_CORE} python detect.py
}

function stop_lwm(){
	pid=`ps -ef | grep detect.py | head -1 | awk '{print $2}'`
	kill -9 $pid
}
