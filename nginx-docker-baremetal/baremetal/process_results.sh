#!/bin/bash

declare -a workConnections=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144)
declare -a threads=(1 4 8 16 32 48) # Number of threads
declare -a nginxCores=(1 4 8 16 32 48) # for file manipulation
declare -a wrkCores=(1 4 8 16 32 48) 

cd res

for wrkCore in "${!wrkCores[@]}"; do
	for nginxCore in "${!nginxCores[@]}"; do
		echo "wrkCores nginxCores Connections Latency  Avg  Stdev  Max  +/-Stdev"
		for workConnection in "${!workConnections[@]}"; do

			echo $(echo ${wrkCores[wrkCore]};  echo ${nginxCores[nginxCore]}; echo ${workConnections[workConnection]};  grep -ir "Latency" clientWorker_${wrkCores[wrkCore]}_nginx_${nginxCores[nginxCore]}_connections_${workConnections[workConnection]}_threads_${wrkCores[wrkCore]}.txt)

		done
	done
done


for wrkCore in "${!wrkCores[@]}"; do
        for nginxCore in "${!nginxCores[@]}"; do
                echo "wrkCores nginxCores Connections Requests/Sec"
                for workConnection in "${!workConnections[@]}"; do

                        echo $(echo ${wrkCores[wrkCore]};  echo ${nginxCores[nginxCore]}; echo ${workConnections[workConnection]};  grep -ir "Requests/Sec" clientWorker_${wrkCores[wrkCore]}_nginx_${nginxCores[nginxCore]}_connections_${workConnections[workConnection]}_threads_${wrkCores[wrkCore]}.txt)

                done
        done
done

