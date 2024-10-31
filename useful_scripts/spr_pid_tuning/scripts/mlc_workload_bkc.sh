function invalind_params()
{
echo "./workload.sh on [S0|S1] [core_list_for_HP]"
echo "S0/S1:workload on Socket0 or Socket1"
echo "core_list_for_HP:core list for High priority TASK.Low priority work load on 32 cores"
echo "Samples:"
echo "1)run 2 MLC workloads on S0 with 2 MEM CLOS:"
echo "./workload.sh S0"
echo "2)run 2 MLC workload on S1, specify the core 32-47 to HP workload"
echo "./workload.sh S1 32-47"

exit 1
}

TIME=380

cores_per_socket=0
numa_node0_1st_core=0
numa_node1_1st_core=0
numa_node0_1st_core_2nd_group=0
numa_node1_1st_core_2nd_group=0

function cpu_topo_scan()
{

cores_per_socket=`lscpu |grep "Core(s) per socket"|awk '{print $ 4}'`

numa_node0_1st_core=`lscpu |grep "NUMA node0 CPU(s)"|awk -F'[- ,]'  '{print $8}'`
numa_node1_1st_core=`lscpu |grep "NUMA node1 CPU(s)"|awk -F'[- ,]'  '{print $8}'`


numa_node0_1st_core_group2=`lscpu |grep "NUMA node0 CPU(s)"|awk -F'[- ,]' '{print $10}'`
numa_node1_1st_core_group2=`lscpu |grep "NUMA node1 CPU(s)"|awk -F'[- ,]' '{print $10}'`


echo "NUMA node0" $numa_node0_1st_core "-" $numa_node0_1st_core_group2
echo "NuMA node1" $numa_node1_1st_core "-" $numa_node1_1st_core_group2

}

function benchmark()
{
        core=$1
        tag=$2
        score=$(mlc --loaded_latency -R -t${TIME} -T -k${core} -d0 | grep 00000 | awk '{print $3}')

        echo ============${tag} = ${score}===============
}

function col()
{

        benchmark $LP_CORES lp &
        benchmark $HP_CORES hp
        sleep 2
}


cpu_topo_scan

if [ $# -eq 0 ]; then

invalind_params

elif [ $# -eq 1 ]; then
  if [ $1 == "S0" ];then
  echo "workload on Socket 0"
  #50%-50% cores on HP and LP
  HP_CORES="0-"$(($cores_per_socket /2 - 1 ))","$numa_node0_1st_core_group2"-""$(($numa_node0_1st_core_group2+ ($cores_per_socket /2 )- 1 ))"
  LP_CORES=$(($cores_per_socket /2))"-"$(($cores_per_socket - 1 ))","$(($numa_node0_1st_core_group2+ ($cores_per_socket /2 )))"-"$(( $numa_node0_1st_core_group2 + $cores_per_socket - 1 ))
 
  elif [ $1 == "S1" ];then 
  echo "workload on Socket 1"

  HP_CORES=$numa_node1_1st_core"-"$(($numa_node1_1st_core + $cores_per_socket /2 - 1 ))","$numa_node1_1st_core_group2"-""$((numa_node1_1st_core_group2+ ($cores_per_socket /2 )- 1 ))"
  LP_CORES=$(($numa_node1_1st_core + $cores_per_socket /2))"-"$(($numa_node1_1st_core + $cores_per_socket - 1 ))","$(($numa_node1_1st_core_group2 + ($cores_per_socket /2 )))"-"$(( $numa_node1_1st_core_group2 + $cores_per_socket - 1 ))

  else
  invalind_params
  fi
else
invalind_params
fi

echo "HP_CORES="$HP_CORES
echo "LP_CORES="$LP_CORES

echo "====MLC HP+LP mix===="
col

