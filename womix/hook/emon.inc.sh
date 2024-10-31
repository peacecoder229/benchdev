echo === Enabling EMON ===

cd /opt/intel/sep/sepdk/src/
./insmod-sep
source /opt/intel/sep/sep_vars.sh
# source /opt/intel/sep/sep_vars.sh emon_api
cd -
CPUSET_FOR_EMON=3

# for CLX only
EMON_CONF="tool/emon-conf/icx"

function start_emon()
{
	emon_file_path=$1
	mkdir -p $emon_file_path

	emon -v > $emon_file_path/emon-v.dat
	emon -M > $emon_file_path/emon-m.dat
	cp $EMON_CONF/metrics.xml $emon_file_path/metrics.xml 
	
	taskset -c $CPUSET_FOR_EMON emon -i $EMON_CONF/events.txt > $emon_file_path/emon.dat &

}

function stop_emon()
{
	emon -stop
}

hook_start_test="start_emon"
hook_finish_test="stop_emon"