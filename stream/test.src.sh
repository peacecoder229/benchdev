#!/bin/bash

# This file is the include head
#  

# disable SElinux for Redhat/Centos/fedora
setenforce 0

# $CMD contains the whole cli commands
CMD=$0 $*

# identify the platfor is skx or bdw
PLAFORM="skx"
TOTAL_LLC_WAYS=11

# bdw's L2 alway 1024
l2_size=`lscpu | grep L2 | grep 1024 | wc -l `

if [ $l2_size -eq 0 ]
then
	TOTAL_LLC_WAYS=20
	PLAFORM="bdw"
fi
# import sources
source src/workload.src.sh
source src/monitor.src.sh
source src/controller.src.sh
