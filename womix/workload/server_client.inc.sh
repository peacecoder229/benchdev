
CLIENT_CPUS=0-7 # fix clients to another NUMA nodes is strongly suggested
echo === set CLIENT_CPUS=${CLIENT_CPUS} ===

MEMTIER_RUN_TIME=300

MEMTIER_DEFAULT_CONF_REDIS="--pipeline=30 -c 16 -t 1 -d 128 --key-maximum=42949 --key-pattern=G:G --key-stddev=1177 --ratio=1:1 --distinct-client-seed --random-data --run-count=1 --hide-histogram --test-time=${MEMTIER_RUN_TIME}"
MEMTIER_DEFAULT_CONF_MEMCACHE="--pipeline=4 -c 16 -t 1 -d 128 -n 1048576 --key-pattern G:G --key-maximum 1500001 --key-pattern=G:G --key-stddev=1177 --ratio=1:1 --distinct-client-seed --random-data --run-count=1 --hide-histogram --test-time=${MEMTIER_RUN_TIME}"

function singleredis()
{
	# installed by yum install redis
	cpuset=$1 
	result_path=$2 
	instance=$3 # useless in this function 
	name=$4
	echo $MEMTIER_DEFAULT_CONF_REDIS > $result_path/memtier_para.txt
	taskset -c $cpuset redis-server &
	taskset -c $CLIENT_CPUS memtier $MEMTIER_DEFAULT_CONF_REDIS --json-out-file=$result_path/result.json 2> $result_path/redis-single.log 

	pkill -9 redis-server

}

function multiredis()
{
	# installed by yum install redis
	cpuset=$1 
	result_path=$2 
	instance=$3 
	name=$4
	echo $MEMTIER_DEFAULT_CONF_REDIS > $result_path/memtier_para.txt
	for i in $(seq $instance)
	do
		taskset -c $cpuset redis-server --port $((6300+$i)) &
	done

	sleep 1

	for i in $(seq $instance)
	do
		taskset -c $CLIENT_CPUS memtier -p $((6300+$i)) $MEMTIER_DEFAULT_CONF_REDIS --json-out-file=$result_path/result_$i.json 2> $result_path/redis-core_$i.log 
	done

	pkill -9 redis-server

}

function memcachedserver()
{
	# installed by yum install memcached
	cpuset=$1 
	result_path=$2 
	instance=$3 
	name=$4
	echo $MEMTIER_DEFAULT_CONF_MEMCACHE > $result_path/memtier_para.txr
	taskset -c $cpuset memcached -t $instance -u root & 
	taskset -c $CLIENT_CPUS memtier_benchmark -p 11211 -P memcache_text $MEMTIER_DEFAULT_CONF_MEMCACHE --json-out-file=$result_path/result.json  2> $result_path/memcached.log 

	pkill -9 memcached 

}
