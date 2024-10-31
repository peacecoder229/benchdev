#!/bin/bash

rm -rf res
mkdir res
declare -a workConnections=(32 64 128 160 256 512 1024 2048) # Number of connections
declare -a nginxWorkers=(0 0-3 0-7 0-15 0-31 0-47) # Server Cores Used
declare -a clientWorkers=(48 48-51 48-55 48-63 48-80 48-95) # Client Cores
declare -a threads=(1 4 8 16 32 48 96) # Number of threads
declare -a cores=(1 4 8 16 32 48) # for file manipulation

echo "Starting Nginx Connection Scaling Performance Testing \n"

echo "Launching 1 Nginx Server + 1 Worker with 32 Connections"

#Nginx Recommends to run at 3mins for stable results


source start-nginx.sh 0 9090
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48 ./wrk/wrk -t 1 -c 32 -d 300s -L http://127.0.0.1:9090/1kb.bin 
numactl --membind=1 --physcpubind=32 ./wrk/wrk -t 1 -c 96 -d 300s -L http://127.0.0.1:9090/1K


source start-nginx.sh 0-3 9090
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48-51 ./wrk/wrk -t 4 -c 128 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-35 ./wrk/wrk -t 4 -c 400 -d 300s -L http://127.0.0.1:9090/1K

source start-nginx.sh 0-7 9090
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48-55 ./wrk/wrk -t 8 -c 224 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-39 ./wrk/wrk -t 8 -c 800 -d 300s -L http://127.0.0.1:9090/1K

source start-nginx.sh 0-15 9090
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48-63 ./wrk/wrk -t 16 -c  -d 336s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-47 ./wrk/wrk -t 16 -c 1120 -d 300s -L http://127.0.0.1:9090/1K


source start-nginx.sh 0-31 9090
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48-79 ./wrk/wrk -t 32 -c 224 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-63 ./wrk/wrk -t 32 -c 1152 -d 300s -L http://127.0.0.1:9090/1K



