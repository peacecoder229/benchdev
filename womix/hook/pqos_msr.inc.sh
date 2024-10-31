echo === Enabling pqos monitoring ===

# core which would run pqos tool
PQOS_CORE=1
# PQOS_OS_INTERFACE=0

function start_pqos()
{
	pqos_file_path=$1
	mkdir -p $pqos_file_path
	
	dmesg -c 
        
	taskset -c $PQOS_CORE pqos -s > $pqos_file_path/rdt_stat_begin.txt
	
    if [ $CORE_1 ]
    then 
		taskset -c $PQOS_CORE pqos -r -m all:[$CORE_1][$CORE_2][$CORE_3][$CORE_4] -o $pqos_file_path/pqos_out.csv -u csv &
	else
	
		taskset -c $PQOS_CORE pqos -r -m all:[$HP_CORES][$LP_CORES] -o $pqos_file_path/pqos_out.csv -u csv &
	fi
}

function stop_pqos()
{
	pkill -9 pqos
	
	dmesg -c > $pqos_file_path/dmesg.txt
	taskset -c $PQOS_CORE pqos -s > $pqos_file_path/rdt_stat_end.txt
}

hook_start_test="start_pqos"
hook_finish_test="stop_pqos"
