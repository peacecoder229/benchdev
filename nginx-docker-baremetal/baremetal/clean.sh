#!/bin/bash

rm -f /var/log/nginx/*
rm -f /root/nginx_vanilla/logs/*
pkill -9 nginx

ulimit -n 66565
echo 3 > /proc/sys/vm/drop_caches && swapoff -a && swapon -a && printf '\n%s\n' 'Ram-cache and Swap Cleared'
sleep 2

