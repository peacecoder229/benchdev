echo ===import HWDRC test logic===

source controller/hwdrc.inc.sh

echo ===import workload list===

source workload/container_based.inc.sh
# source workload/mlc.inc.sh
# source workload/server_client.inc.sh

echo +++ enable resctrl +++
pqos -s -I

hook_start_test="empty"
hook_finish_test="empty"

function run_hp()
{
	data_folder=$2/hp
	workload=$1

	mkdir -p $data_folder

	$workload $HP_CORES $data_folder $HP_INSTANCES "HP" &
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

function set_restctl()
{
	container_name=$1
	restctl_path=$2

	container_id=$(docker ps -f name=${container_name} -q)

	cgroup_base="/sys/fs/cgroup/cpu/docker/"
	tasks=$( find ${cgroup_base}/${container_id}* -name "tasks")

	if [ ! -f $tasks ]
	then
		return
	fi

	echo "Container ${container_name} is set to  $(basename $restctl_path)"
	for pid in $(cat ${tasks})
	do
		echo $pid > $restctl_path/tasks
	done

}

function set_rdt()
{
	set_restctl "HP" $HP_COS &
	set_restctl "LP" $LP_COS &
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

    sleep 5
	set_rdt

	wait_docker_stop

	$hook_finish_test $path
}

HP_COS="/sys/fs/resctrl/COS4"
LP_COS="/sys/fs/resctrl/COS7"

function workload_pair_restctl()
{
	mkdir -p $HP_COS
	mkdir -p $LP_COS

	hp=$1
	lp=$2 

	ROOT=HWDRCRestctl/`date +WW%W.%u`/$hp-$lp
	
	initial_settings
	start_workloads $hp $lp  $ROOT/00_non

	for LP_MBA in $(seq 10 10 90)
	do
		initial_settings
		echo "MB:0=${LP_MBA};1=${LP_MBA}" > $LP_COS/schemata
		start_workloads $hp $lp  $ROOT/01_rdt_MBA$LP_MBA
		# start_workloads $hp_workload $lp_workload  $ROOT/01_rdt_MBA$LP_MBA
	done

	# initial_settings
	# echo "MB:0=${LP_MBA};1=${LP_MBA}" > $LP_COS/schemata
	# start_workloads $hp $lp  $ROOT/01_rdt

	initial_settings
	python2 hwdrc_postsi/hwdrc_config.py init 0
	echo "MB:0=100;1=100" > $LP_COS/schemata
	start_workloads $hp $lp $ROOT/03_hwdrc

	cp $0 $ROOT/$0

	rmdir $HP_COS
	rmdir $LP_COS
}
