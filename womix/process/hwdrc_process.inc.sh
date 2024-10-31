echo ===import HWDRC test logic===

source controller/hwdrc.inc.sh

echo ===import workload list===

source workload/container_based.inc.sh
source workload/mlc.inc.sh
source workload/server_client.inc.sh


hook_start_test="empty"
hook_finish_test="empty"

function run_hp()
{
	data_folder=$2/hp
	workload=$1

	mkdir -p $data_folder

	$workload $HP_CORES $data_folder $HP_INSTANCES "HP"
}

function run_lp()
{
	data_folder=$2/lp
	workload=$1

	mkdir -p $data_folder

	$workload $LP_CORES $data_folder $LP_INSTANCES "LP" & 
}


KEEP_LP_RUNNING=1
function wait_docker_stop()
{
	if [ $KEEP_LP_RUNNING -eq 1 ]
	then
		sleep 1
		while [ $(docker ps -q | wc -l) -gt 0 ]
		do
			sleep 3
		done
	else
		stop_all_dockers
	fi
}

function stop_all_dockers()
{
	docker stop $(docker ps -qa)
}

function baseline()
{
	hp=$1
	path=$2

	sync
	echo 1 >       /proc/sys/vm/drop_caches
	
	$hook_start_test $path
	run_hp $hp $path

	wait_docker_stop
	$hook_finish_test 

}


function start_workloads()
{
	hp=$1
	lp=$2
	path=$3

	sync
	echo 1 >       /proc/sys/vm/drop_caches

	$hook_start_test $path

	run_lp $lp $path
	run_hp $hp $path
	
	wait_docker_stop

	$hook_finish_test $path
}

function workload_pair()
{

	hp_workload=$1
	lp_workload=$2

	ROOT=HWDRCValidation/`date +WW%W.%u`/$hp_workload-$lp_workload
	mkdir -p $ROOT
	cp $0 $ROOT/$0
	
	initial_settings
	# full contention
	start_workloads $hp_workload $lp_workload  $ROOT/00_non 
	start_workloads $hp_workload "empty" $ROOT/05_hponly

	# set_rdt
	# start_workloads $hp_workload $lp_workload  $ROOT/01_rdt

	# set_swdrc
	# start_workloads $hp_workload $lp_workload  $ROOT/02_swdrc

	set_hwdrc
	hwdrc_debug $ROOT/03_hwdrc
	# HWDRC
	start_workloads $hp_workload $lp_workload $ROOT/03_hwdrc
	# HP only
	start_workloads $hp_workload "empty" $ROOT/04_hponly-hwdrc
}

function mba_scaling()
{

	hp_workload=$1
	lp_workload=$2

	ROOT=HWDRCValidation/`date +WW%W.%u`/$hp_workload-$lp_workload
	# ROOT=RDTTune/`date +WW%W.%u`/$hp_workload-$lp_workload
	mkdir -p $ROOT
	cp $0 $ROOT/$0

	for LP_MBA in $(seq 10 10 90)
	do
		set_rdt
		start_workloads $hp_workload $lp_workload  $ROOT/01_rdt_MBA$LP_MBA
	done

}

# function full_colocation()
# {
# 	ROOT=`date +WW%W.%w-%H%M`-$1
	
# 	for hp_workload in `cat hp_workload.txt`
# 	do

# 		baseline $hp_workload $ROOT/hp-only

# 		for lp_workload in `cat lp_workload.txt`
# 		do
# 			start_workloads $hp_workload $lp_workload $ROOT/$hp_workload-$lp_workload
# 		done
# 	done
# }

# function drc_impaction_demo()
# {
# 	ROOT=`date +WW%W.%w-%H%M`-MLC

# 	hp_workload=mlc_benchmark
# 	lp_workload=mlc_benchmark

# 	initial_settings
# 	start_workloads $hp_workload $lp_workload  $ROOT/base

# 	set_rdt
# 	for mba in $(seq 10 10 100)
# 	do
# 		pqos -e mba:1=$mba
# 		start_workloads $hp_workload $lp_workload  $ROOT/mba_$mba
# 	done

# 	# set_swdrc
# 	# start_workloads $hp_workload $lp_workload  $ROOT/02_swdrc

# 	set_hwdrc
# 	start_workloads $hp_workload $lp_workload $ROOT/hwdrc

# }
