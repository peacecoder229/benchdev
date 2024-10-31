#!/bin/bash

rm -rf res
mkdir res
declare -a workConnections=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 262144) # Number of connections
declare -a nginxWorkers=(0 0-3 0-7 0-15 0-31 0-47) # Server Cores Used
declare -a clientWorkers=(48 48-51 48-55 48-63 48-80 48-95) # Client Cores
declare -a threads=(1 4 8 16 32 48 96) # Number of threads
declare -a cores=(1 4 8 16 32 48) # for file manipulation

echo "Starting Nginx Connection Scaling Performance Testing \n"

for clientWorker in "${!clientWorkers[@]}" ;do
	echo "clientWorker:" $clientWorker ${clientWorkers[clientWorker]}
	for nginxWorker in "${!nginxWorkers[@]}" ;do
		echo "nginxWorker" $nginxWorker ${nginxWorkers[nginxWorker]}
		for workConnection in "${!workConnections[@]}"; do	
			echo "workConnection" $workConnection ${workConnections[workConnection]} "Threads: " ${threads[clientWorker]}
			source start-nginx.sh ${nginxWorkers[nginxWorker]} 80
			P1=$!
			wait $P1
			#echo "Threads: " ${threads[clientWorker]}	
			numactl --membind=1 --physcpubind=${clientWorkers[clientWorker]} ./wrk/wrk -t ${threads[clientWorker]} -c ${workConnections[workConnection]} -d 180s http://127.0.0.1:80/1kb.bin > res/clientWorker_${cores[clientWorker]}_nginx_${cores[nginxWorker]}_connections_${workConnections[workConnection]}_threads_${threads[clientWorker]}.txt
			
			rm -f /var/log/nginx/*
			rm -f /root/nginx_vanilla/logs/*
			killall -9 nginx
		done
	done
done
