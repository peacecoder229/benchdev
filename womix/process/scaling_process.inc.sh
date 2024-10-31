

echo ===import scaling test logic===

source controller/rdt.inc.sh
source controller/freq.inc.sh

source workload/container_based.inc.sh
source workload/mlc.inc.sh

hook_start_test="empty"
hook_finish_test="empty"

function run_hp()
{
	data_folder=$2/hp
	workload=$1
	ins=$3
	cpuset=$4

	mkdir -p $data_folder

	$workload $cpuset $data_folder $ins
}


function wait_docker_stop()
{
	sleep 1
	while [ $(docker ps -q | wc -l) -gt 0 ]
	do
		sleep 3
	done
}

function start_baseline()
{
	hp=$1
	path=$2
	ins=$3
	cpuset=$4

	sync
	echo 1 >       /proc/sys/vm/drop_caches
	
	$hook_start_test $path
	run_hp $hp $path $ins $cpuset

	wait_docker_stop
	$hook_finish_test $path

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

DEFAULT_COS=7 # COS is 7
function start_with_rdt()
{
    cpuset=$1
    workload=$2
    instance=$3
    path=$4

    cat=$5
    mba=$6

    set_cos_rdt $cpuset $DEFAULT_COS $cat $mba
    start_baseline $workload $path $instance $cpuset

}

function start_with_freq()
{
    cpuset=$1
    workload=$2
    instance=$3
    path=$4

    freq=$5

    set_all_cpu_frequency $freq
    start_baseline $workload $path $instance $cpuset
}

function workload_sweeping_interface()
{
    workload=$1
    instance=$2

    initial_settings
    
    empty

}

function foo_sweeping_interface()
{
    workload=$1
    instance=$2

    # prepare
    initial_settings

    # batch/loop 
    for i in $(seq 1 100)
    do
        echo Run $workload with $instance instance, Loop: $i 
        sleep 1
        echo 
    done
}

# default RDT setting for SKX/CLX/CPX: 1~11 for cat, 100% for mba

CAT_RANGE=$(seq 11) # 1 ~ 11
MBA_RANGE=$(seq 100 100) # 100% only

ROOT_PATH=Scaling/$(date +WW%W.%u)/$WORKLOAD

function rdt_sweeping()
{
    workload=$1
    instance=$2

    initial_settings

    for cat in $CAT_RANGE
    do
        for mba in $MBA_RANGE
        do
            path="${ROOT_PATH}/$workload/CAT${cat}_MBA${mba}"

            start_with_rdt $CPUSET $workload $instance $path $cat $mba

        done
    done
}

function frequency_sweeping()
{
    workload=$1
    instance=$2

    initial_settings

    if ["z${UNCORE_FREQU}" -ne "z"]
    then
        uncore_frequency $UNCORE_FREQU
    fi

    for freq in $FREQ_RANGE
    do
        path="${ROOT_PATH}/freq${freq}"

        start_with_freq $CPUSET $workload $instance $path $freq
    done
}