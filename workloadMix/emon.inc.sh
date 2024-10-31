
cd /opt/intel/sep/sepdk/src/
./insmod-sep
source /opt/intel/sep/sep_vars.sh emon_api
cd -


function start_emon()
{
	emon_file_path=$1
	mkdir -p $emon_file_path

	emon -v > $emon_file_path/emon-v.dat
	emon -M > $emon_file_path/emon-m.dat
	cp clx-2s.xml $emon_file_path/metrics.xml

	taskset -c 3 emon -i clx-2s-events.txt > $emon_file_path/emon.dat &

}

function stop_emon()
{
	emon -stop
}

hook_start_test="start_emon"
hook_finish_test="stop_emon"


