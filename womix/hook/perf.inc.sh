echo === Enabling PERF ===

PERF_EVENTS="tsc,instructions,cycles"
PERF_INTERVAL=1000
EMON_ENABLE=1

if [ $EMON_ENABLE -eq 1 ]
then
	cd /opt/intel/sep/sepdk/src/
	./insmod-sep
	source /opt/intel/sep/sep_vars.sh
	# source /opt/intel/sep/sep_vars.sh emon_api
	cd -
	CPUSET_FOR_EMON=3
fi



function start_perf()
{
	file_path=$1
	mkdir $file_path

	if [ $EMON_ENABLE -eq 1 ]
	then
		emon -v > $file_path/emon-v.dat
		emon -M > $file_path/emon-m.dat

		emon -l3600 -t1 -C "UNC_M_RPQ_CYCLES_NE.PCH0,UNC_M_RPQ_OCCUPANCY_PCH0" > $file_path/emon.dat & 
	fi
	#else
		perf stat -e ${PERF_EVENTS} -I ${PERF_INTERVAL} -C ${LP_CORES} -o $file_path/perf_lp.csv & 
		perf stat -e ${PERF_EVENTS} -I ${PERF_INTERVAL} -C ${HP_CORES} -o $file_path/perf_hp.csv & 
	#fi
	# RPQ_OCC = UNC_M_RPQ_OCCUPANCY_PCH0 / UNC_M_RPQ_CYCLES_NE.PCH0
	
}

function stop_perf()
{
	if [ $EMON_ENABLE -eq 1 ]
	then
		emon -stop
	fi
	#else
		pkill -9 perf
	#fi

	# pkill -9 perf
}

hook_start_test="start_perf"
hook_finish_test="stop_perf"
