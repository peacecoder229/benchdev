
# Turn-off the hyper-threading

echo off > /sys/devices/system/cpu/smt/control 


# Server Terminal for Different Sockets


sysctl -w net.ipv4.tcp_max_syn_backlog=6553600
sysctl -w net.core.wmem_max=838860800
sysctl -w net.core.rmem_max=838860080
sysctl -w net.core.somaxconn=5120000
sysctl -w net.core.optmem_max=8192000



cgcreate -g cpuset:drs-cgroup

echo 0-59 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.cpus

echo 0 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/drs-cgroup/tasks

taskset -c 0-59 nginx -c nginx_custom.conf

# Client Terminal for Different Sockets

cgcreate -g cpuset:wrk-cgroup

echo 60-119 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.cpus

echo 1 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/wrk-cgroup/tasks

taskset -c 60-119 ./wrk -c 5000 -t 60 -d 60s http://127.0.0.1:8081/1kb.bin -R 680000


# Server Terminal for Same Socket

sysctl -w net.ipv4.tcp_max_syn_backlog=6553600
sysctl -w net.core.wmem_max=838860800
sysctl -w net.core.rmem_max=838860080
sysctl -w net.core.somaxconn=5120000
sysctl -w net.core.optmem_max=8192000



cgcreate -g cpuset:drs-cgroup

echo 0-59 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.cpus

echo 0 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/drs-cgroup/tasks

taskset -c 0-59 nginx -c nginx_custom.conf


# Client Terminal for Same Socket

cgcreate -g cpuset:wrk-cgroup

echo 60-119 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.cpus

echo 0 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/wrk-cgroup/tasks

taskset -c 60-119 ./wrk -c 5000 -t 60 -d 60s http://127.0.0.1:8081/1kb.bin -R 680000


# Server Terminal for Different Socket 30 Cores

cp nginx_custom_30.conf /usr/share/nginx/nginx_custom.conf

sysctl -w net.ipv4.tcp_max_syn_backlog=6553600
sysctl -w net.core.wmem_max=838860800
sysctl -w net.core.rmem_max=838860080
sysctl -w net.core.somaxconn=5120000
sysctl -w net.core.optmem_max=8192000



cgcreate -g cpuset:drs-cgroup

echo 0-29 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.cpus

echo 0 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/drs-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/drs-cgroup/tasks

taskset -c 0-29 nginx -c nginx_custom.conf


# Client Terminal for Different Socket 30 Cores

cgcreate -g cpuset:wrk-cgroup

echo 60-89 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.cpus

echo 1 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mems

echo 1 > /sys/fs/cgroup/cpuset/wrk-cgroup/cpuset.mem_hardwall

echo $$ > /sys/fs/cgroup/cpuset/wrk-cgroup/tasks

taskset -c 60-89 ./wrk -c 5000 -t 30 -d 60s http://127.0.0.1:8081/1kb.bin -R 680000





