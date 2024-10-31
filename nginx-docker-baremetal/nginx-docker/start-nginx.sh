#!/bin/bash 

#sysctl -w net.ipv4.tcp_max_syn_backlog=6553600
#sysctl -w net.core.wmem_max=838860800
#sysctl -w net.core.rmem_max=838860080
#sysctl -w net.core.somaxconn=5120000
#sysctl -w net.core.optmem_max=8192000
#
ulimit -n 66565

cd /root

echo "worker_processes  ${NGINX_CORE};" >> nginx_custom.conf

service supervisor start

nginx -c /root/nginx_custom.conf &

/bin/bash
