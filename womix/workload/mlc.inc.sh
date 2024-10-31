MLC_OPERATION="R"
MLC_DURATION=300

function mlc_benchmark()
{
	# copy mlc to /usr/bin 
	
	cpuset=$1 # str CPUSET
	result_path=$2 # path contain result files, will be auto created
	instance=$3 #instance number, thread numbers (or other values needed)
	name=$4
	
    mlc --loaded_latency -$MLC_OPERATION -t$MLC_DURATION -T -k$cpuset -d0 | grep 00000 | awk '{print $3}'  > $result_path/mlc_out.txt

}
