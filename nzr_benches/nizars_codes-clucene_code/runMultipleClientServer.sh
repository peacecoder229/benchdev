#!/bin/sh

# write max, min, avg of client and server in summary log
summary_log() {
 x=1
}

if [ $# != 4 ]; then
    echo "Usage: ./runMultipleClient.sh <#ofServers> <#ofClients> <#ofThreads> <runTime>"
    echo "Note that <#ofClients> should be a multiple of <#ofServers>."
    exit 1
fi

# clean up logs from previous runs
rm -f Server_*
rm -f Client_*
rm -f Search_result_*
rm -f Summary_*
rm -f Combined_*
rm -f phrase_query_file_*
rm -f term_query_file_*

# from args
noOfServers=$1
noOfClients=$2
noOfThreads=$3
run_time=$4

# server args
topk=5
serverBasePort=47001
serverIp="127.0.0.1"

if ((noOfClients % noOfServers == 0)); then
    clientPerServer=$((noOfClients / noOfServers))
else
    echo "<#ofClients> should be a multiple of <#ofServers>."
fi

# run emon
emonname=C_${noOfClients}_S_${noOfServers}_NT_${noOfThreads}_RT_${run_time}_TOPK_${topk}
#/pnpdata/clucene_benchmark_new/emon/run_emon.sh $emonname
# vmstat 10 70 > VMSTAT_$emonname &
# run server:
# ./server #ofThreads #run_time(min) topk test_name(t, c, tc, tpc)
# index_file_dir portnuber #ofclients
#./server $noOfThreads $run_time $topk t ./index_original_compressed/ &
serverPort=$serverBasePort
corePerServer=$((noOfThreads/noOfServers))
coreStart=1
coreEnd=$((coreStart+corePerServer))
threadPerServer=$((noOfThreads/noOfServers))
for (( serverId = 0; serverId < $noOfServers; serverId++))
do
    taskset -c --cpu-list $coreStart-$coreEnd  perf record ./serverMultiThread $noOfThreads $run_time $topk c $serverIp $serverId $serverPort $clientPerServer &
    #echo "taskset --cpu-list $coreStart-$coreEnd ./serverMultiThread $threadPerServer $run_time $topk c $serverIp $s    erverId $serverPort $clientPerServer &"
    #taskset --cpu-list $coreStart-$coreEnd ./serverMultiThread $threadPerServer $run_time $topk c $serverIp $serverId $serverPort $clientPerServer &
    echo "Server#$serverId($coreStart-$coreEnd) is listening on port#$serverPort"
    serverPort=$((serverPort + 1))
    coreStart=$((coreEnd+1))
    coreEnd=$((coreStart+corePerServer))
done

# run clients:
server=0
serverPort=$serverBasePort
coreNo=17
for (( client = 0; client < $noOfClients; client++ ))
do
    #./client hostname portnumber(server) clientId
    cp phrase_query_file phrase_query_file_$client
    cp term_query_file term_query_file_$client
    taskset -c $coreNo ./client $serverIp $serverPort $client &
    echo "Client#$clienti($coreNo) will request to Server#$server on port $serverPort"
    
    if ! (( $((client+1)) % $clientPerServer )); then
        server=$((server+1))
        serverPort=$((serverPort+1))
    fi
    if [ $coreNo -eq 30 ]; then
        coreNo=48
    else
        coreNo=$((coreNo + 1))
    fi
done

wait
#source /opt/intel/sep/sep_vars.sh
#emon -stop
echo "Experiment Done. Combining log now...."
#echo "# of Servers, # of Clients, Server avg QPS"

#mv perf.data  Perf_$emonname.data

totalQuery=0
for i in $(ls | grep Server_Query); do
    queryCount=$(wc -l $i | cut -d' ' -f1)
    totalQuery=$((totalQuery+queryCount))
done

qps=$((totalQuery/(noOfServers*run_time*60)))

echo "QueryTag,SearchStart" >> Server_Search_Start_Combine.log
cat $(ls | grep Server_Search_Start_) >> Server_Search_Start_Combine.log

echo "QueryTag,SearchEnd" >> Server_Search_End_Combine.log
cat $(ls | grep Server_Search_End_) >> Server_Search_End_Combine.log

echo "QueryTag,QueueStart" >> Server_Queue_Start_Combine.log
cat $(ls | grep Server_Queue_Start_) >> Server_Queue_Start_Combine.log

echo "QueryTag,QueueEnd" >> Server_Queue_End_Combine.log
cat $(ls | grep Server_Queue_End_) >> Server_Queue_End_Combine.log

echo "QueryTag,RTT(us)" >> Client_Rtt_Combine.log
cat $(ls | grep Client_RTT_) >> Client_Rtt_Combine.log
