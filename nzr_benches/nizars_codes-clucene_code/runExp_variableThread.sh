#!/bin/sh

noOfServers=1
noOfClients=2
run_time=1
declare -a noOfThreads=(1)
topk=5
serverIp="127.0.0.1"

expCombinedFileName=Search_WorkLoad_C_constant_S_Constant_NT_variable_RT_${run_time}_TOPK_${topk}.csv

if [[ ! -e $expCombinedFileName ]]; then
    echo "# of Clients, # of Servers, # of Search Thread, Server avg QPS, Server avg Searchtime(us), Server avg Queue Delay(us), Client avg RTT(us)" > $expCombinedFileName
fi

for (( i = 0; i < ${#noOfThreads[@]}; ++i))
do
    ./runMultipleClientServer.sh $noOfServers $noOfClients ${noOfThreads[i]} $run_time &
    # wait for the experiment to finish before processing logs
    #wait
    sleep ${run_time}m
    sleep 30s
    # run the python script which will process the logs create in the run
    threadPerServer=$((${noOfThreads[i]}/noOfServers))
    python3 processCsv_2.py $noOfServers $noOfClients $expCombinedFileName $run_time $noOfThreads
    
    sleep 10s
    #gprof serverMultiThread > Gmon_Unlogged_Search_WorkLoad_C_variable_S_variable_NT_${noOfThreads}_RT_${run_time}_TOPK_${topk}.out
done
