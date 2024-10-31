#!/bin/bash

ulimit -n 66565
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 1

cd wrk

#Configuration for wrk suggested here https://www.nginx.com/blog/nginx-plus-sizing-guide-how-we-tested/#nginx-plus-release-7-r7

for i in `seq $1 $2`; do
    #echo $i	
    taskset -c $i ./wrk -t 1 -c 50 -d 20s  http://127.0.0.1:80/1kb.bin &
done

cd -
