#!/bin/bash
source process/restctl_process.inc.sh
# source hook/pqos_msr.inc.sh
# source hook/emon.inc.sh

ALL_CORES=$(lscpu | grep NUMA | tail -1  | awk '{print $4}')
core_count=$(lscpu | grep "Core(s) per socket:" | tail -1  | awk '{print $4}')
HP_INSTANCES=$core_count
LP_INSTANCES=$core_count

LP_MBA=10

workload_pair_restctl $1 $2
