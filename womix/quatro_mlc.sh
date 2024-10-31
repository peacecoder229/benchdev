#!/bin/bash

source process/quatro_process.inc.sh
#source hook/pqos_msr.inc.sh
source hook/emon.inc.sh


CORE_1=32-39
CORE_2=40-47
CORE_3=48-55
CORE_4=56-63

INSTANCE_1=8
INSTANCE_2=8
INSTANCE_3=8
INSTANCE_4=8

workload=mlc_benchmark
workload_quatro $workload
