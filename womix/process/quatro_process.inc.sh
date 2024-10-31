echo ===import HWDRC test logic===

source controller/hwdrc.inc.sh

echo ===import workload list===

# source workload/container_based.inc.sh
source workload/mlc.inc.sh
# source workload/server_client.inc.sh


hook_start_test="empty"
hook_finish_test="empty"

function run_hp()
{
	data_folder=$2
	workload=$1

	mkdir -p $data_folder

	$workload $HP_CORES $data_folder $HP_INSTANCES
}

function run_lp()
{
	data_folder=$2
	workload=$1
	mkdir -p $data_folder

	$workload $LP_CORES $data_folder $LP_INSTANCES & 
}

hook_start_test="empty"
hook_finish_test="empty"
function start_workloads()
{
    workload=$1
    d=$2
    for i in $(seq 4)
    do
		mkdir -p ${d}/group${i}
    done

    $hook_start_test $d

    $workload $CORE_2 ${d}/group2 $INSTANCE_2 "G2" &
    $workload $CORE_3 ${d}/group3 $INSTANCE_3 "G3" &
    $workload $CORE_4 ${d}/group4 $INSTANCE_4 "G4" &
    
    $workload $CORE_1 ${d}/group1 $INSTANCE_1 "G1"
	
	sleep 3
	$hook_finish_test $d
	
}

COS_1=4
COS_2=7
COS_3=5
COS_4=6

LP_MBA=10

function workload_quatro()
{

	workload=$1

	ROOT=HWDRC4Workloads/`date +WW%W.%u`/$workload
	mkdir -p $ROOT
	cp $0 $ROOT/$0

        HP_CORES=$CORE_1	
        LP_CORES=$CORE_2	

	initial_settings
	start_workloads $workload ${ROOT}/00_non

	set_rdt
    pqos -a core:$COS_3=$CORE_3
	pqos -e mba:$COS_3=30
    pqos -a core:$COS_4=$CORE_4
	pqos -e mba:$COS_4=50

	start_workloads $workload ${ROOT}/01_rdt

	set_hwdrc
    pqos -a core:$COS_3=$CORE_3
    pqos -a core:$COS_4=$CORE_4

	start_workloads $workload ${ROOT}/03_hwdrc

	if [ $workload == "mlc_benchmark" ]
	then
		read_mlc ${ROOT}/00_non Baseline
		read_mlc ${ROOT}/01_rdt RDT
		read_mlc ${ROOT}/03_hwdrc HWDRC
	fi
}

function read_mlc()
{
	echo "For $2 results:"
	for i in $(seq 4)
	do
		score=$(cat $1/group$i/mlc_out.txt)
		echo "		GROUP${i} = ${score}"
	done
}
