# this is an example form workload pack
function workload_interface()
{
	cpuset=$1 # str CPUSET
	result_path=$2 # path contain result files, will be auto created
	instance=$3 #instance number, thread numbers (or other values needed)
    name=$4
	
	# cmd for workload starting
	sleep 0 > /dev/null 
}
