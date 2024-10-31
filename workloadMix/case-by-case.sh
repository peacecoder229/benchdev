#!/bin/bash 

source ./test_process.inc.sh 
# # enable emon here
#source ./emon.inc.sh

HP_CORES=24-35,72-83
LP_CORES=36-47,84-95

DEFAULT_CAT=0x7ff

./hwpdesire.sh -f 2100000

# #disable cstat
# for cstat in `seq 1 3`
# do
#         cpupower idle-set -d $cstat
# done

for hp in `cat hp_wl.txt`
do
	for lp in `cat lp_wl.txt`
	do
		workload_pair $hp $lp
	done
done
