#!/bin/bash

port=$5
rm -f  /usr/share/nginx/nginx_custom_$port.conf
cd  /root/wrk2
sleep 5
lcore=$1
phys_hi=$(echo $lcore | cut -d- -f2)
phys_lo=$(echo $lcore | cut -d- -f1)
count=$(( phys_hi-phys_lo+1 ))
cp -f  /usr/share/nginx/nginx_tmp.conf /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/worker_processes  corecount;/worker_processes  $count;/" /usr/share/nginx/nginx_custom_$port.conf
sed -i "s/listen       10001;/listen       $port;/" /usr/share/nginx/nginx_custom_$port.conf

#arg1 ngxcore arg2 RPS arg3 Connection arg4 clientcore


numactl --membind=0 --physcpubind=$lcore nginx -c  /usr/share/nginx/nginx_custom_$port.conf &
#numactl --membind=0 --physcpubind=$lcore /root/nginx_vanilla/sbin/nginx -c /usr/share/nginx/nginx_custom.conf &
con=$3
RPS=$2
threads=$6
#res=$(./appstatdata.py 32-63 64 32000 120s 1000000 http://127.0.0.1:10001)
#res=$(./appstatdata.py 32-63 64 32000 120s 3000000 http://127.0.0.1:10001)
#./appstatdata.py 32-35 16 $con 60s $RPS http://127.0.0.1:10001/4K
#res=$(./appstatdata.py 32-35 16 $con 60s $RPS http://127.0.0.1:10001/4K)
res=$(./appstatdata.py $4 $threads $con 30s $RPS http://127.0.0.1:$port/1K)
#thread, con, p50, p75, p99, TotalRequests, timeouts
echo $res
cd -


