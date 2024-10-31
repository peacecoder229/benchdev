#!/bin/bash

ulimit -n 66565
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 1

cd wrk2
clientCores=$1
threads=$2
con=$3
RPS=$4
filename=$5
port=$6

echo ""

numactl --membind=$7 --physcpubind=$clientCores ./wrk  -t $threads -c $con -d 15s -R $RPS -L http://127.0.0.1:$port/$filename

cd -
