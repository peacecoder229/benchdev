#!/bin/sh

cp 1kb.bin /usr/share/nginx/html/
cp 4kb.bin /usr/share/nginx/html/
cp 1mb.bin /usr/share/nginx/html/


ulimit -n 66565
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 1

port=$5
rm -f  /usr/share/nginx/nginx_custom_$port.conf

killall -9 nginx

sysctl -w net.ipv4.tcp_max_syn_backlog=6553600
sysctl -w net.core.wmem_max=838860800
sysctl -w net.core.rmem_max=838860080
sysctl -w net.core.somaxconn=5120000
sysctl -w net.core.optmem_max=8192000

rm -f /var/log/nginx/*
rm -f /root/nginx_vanilla/logs/*
#pkill -9 nginx
sleep 5
lcore=$1

phys_hi=$(echo $lcore | cut -d- -f2)
phys_lo=$(echo $lcore | cut -d- -f1)

count=$(( phys_hi-phys_lo+1 ))

cp -f  /usr/share/nginx/nginx_tmp.conf /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/worker_processes  corecount;/worker_processes  $count;/" /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/listen       10001;/listen       $port;/" /usr/share/nginx/nginx_custom_$port.conf

#arg1 ngxcore arg2 RPS arg3 Connection arg4 clientcore
cd wrk2
numactl --membind=0 --physcpubind=$lcore nginx -c  /usr/share/nginx/nginx_custom_$port.conf &
con=$3
RPS=$2
threads=$6
clientCores=$4
filename=$7

echo "Going to run worker process \n"

#res=$(./appstatdata.py $4 $threads $con 240s $RPS http://127.0.0.1:$port/4K)
res=$(./appstatdata.py $clientCores $threads $con 15s $RPS http://127.0.0.1:$port/$filename)
#thread, con, p50, p75, p99, TotalRequests, timeouts
echo $res
cd -

