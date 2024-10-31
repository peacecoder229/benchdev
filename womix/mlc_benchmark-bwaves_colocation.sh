#!/bin/bash

source process/hwdrc_process.inc.sh
source hook/pqos_msr.inc.sh
# source hook/emon.inc.sh

LP_CAT=0xfff
LP_MBA=10 # change it if needed

HP_CORES=32-47,96-111
LP_CORES=48-63,112-127
HP_INSTANCES=32
LP_INSTANCES=32
hp=mlc_benchmark
lp=bwaves
mba_scaling $hp $lp
#KEEP_LP_RUNNING=0
workload_pair $hp $lp
