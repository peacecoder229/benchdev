#!/bin/bash 

echo "Starting Nginx"

killall -9 nginx

ulimit -n 66565
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 1

echo "./start-nginx.sh <number of cores> <port>"

port=$2
rm -f  /usr/share/nginx/nginx_custom_$port.conf

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

worker_process=$(( phys_hi-phys_lo+1 ))

cp nginx_custom.conf /usr/share/nginx/nginx_tmp.conf
cp -f  /usr/share/nginx/nginx_tmp.conf /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/worker_processes  corecount;/worker_processes  $worker_process;/" /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/listen       10001;/listen       $port;/" /usr/share/nginx/nginx_custom_$port.conf

numactl --membind=0 --physcpubind=$lcore nginx -c  /usr/share/nginx/nginx_custom_$port.conf 

