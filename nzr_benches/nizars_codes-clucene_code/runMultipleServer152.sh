#!/bin/bash

noOfServers=8
clientPerServer=2
noOfClients=8

noOfThreads=1
run_time=1
topk=5
serverStartPort=47001
serverIp="172.17.0.1"
serverIpSubnetStart=1

: '
# run server:
# ./server #ofThreads #run_time(min) topk test_name(t, c, tc, tpc)
# index_file_dir portnuber #ofclients
#./server $noOfThreads $run_time $topk t ./index_original_compressed/ &
serverPort=$serverStartPort
for (( serverId = 1; serverId <= $noOfServers; serverId++))
do
    serverIp=
    ./server $noOfThreads $run_time $topk c $serverIp  $serverPort $clientPerServer &
    serverPort=$((serverPort + 1))
    
done
'

#emonname=C_${noOfClients}_S_${noOfServers}_NT_${noOfThreads}_RT_${run_time}_TOPK_${topk}
#/pnpdata/clucene_benchmark_new/emon/run_emon.sh $emonname

serverId=0

taskset -c 1 ./server $noOfThreads $run_time $topk c 192.168.1.99 $((serverId+0)) 47001 $clientPerServer &
taskset -c 2 ./server $noOfThreads $run_time $topk c 192.168.2.99 $((serverId+1)) 47002 $clientPerServer &
taskset -c 3 ./server $noOfThreads $run_time $topk c 192.168.3.99 $((serverId+2)) 47003 $clientPerServer &
taskset -c 4 ./server $noOfThreads $run_time $topk c 192.168.4.99 $((serverId+3)) 47004 $clientPerServer &

taskset -c 5 ./server $noOfThreads $run_time $topk c 192.168.5.99 $((serverId+4)) 47005 $clientPerServer &
taskset -c 6 ./server $noOfThreads $run_time $topk c 192.168.6.99 $((serverId+5)) 47006 $clientPerServer &
taskset -c 7 ./server $noOfThreads $run_time $topk c 192.168.7.99 $((serverId+6)) 47007 $clientPerServer &
taskset -c 8 ./server $noOfThreads $run_time $topk c 192.168.8.99 $((serverId+7)) 47008 $clientPerServer &

#wait

#source /opt/intel/sep/sep_vars.sh
#emon -stop
