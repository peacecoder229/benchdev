
source ./controller.inc.sh
source ./workload.inc.sh

function empty()
{
	sleep 0
}

hook_start_test="empty"
hook_finish_test="empty"

function wait_docker_stop()
{
	sleep 1
	while [ $(docker ps -q | wc -l) -gt 0 ]
	do
		sleep 3
	done
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

	$hook_finish_test 
}

function workload_pair()
{

	hp_workload=$1
	lp_workload=$2

	ROOT=`date +WW%W.%w-%H%M`-$hp_workload-$lp_workload
	
	initial_settings
	start_workloads $hp_workload $lp_workload  $ROOT/00_non

	set_rdt
	start_workloads $hp_workload $lp_workload  $ROOT/01_rdt

	set_swdrc
	start_workloads $hp_workload $lp_workload  $ROOT/02_swdrc

	set_hwdrc
	start_workloads $hp_workload $lp_workload $ROOT/03_hwdrc
}

function full_colocation()
{
	ROOT=`date +WW%W.%w-%H%M`-$1
	
	for hp_workload in `cat hp_workload.txt`
	do

		baseline $hp_workload $ROOT/hp-only

		for lp_workload in `cat lp_workload.txt`
		do
			start_workloads $hp_workload $lp_workload $ROOT/$hp_workload-$lp_workload
		done
	done
}
