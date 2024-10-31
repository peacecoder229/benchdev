#!/bin/bash

echo "Compiling the docker container" 
ulimit -n 66565


docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)
systemctl stop docker
cp override.conf /etc/systemd/system/docker.service.d/.
systemctl start docker
systemctl reload docker
systemctl daemon-reload


docker build -t mynginx . 



docker run --cpuset-cpus=0 -e NGINX_CORE=1 -td -p 80:80 --name nginxtest  mynginx:latest
P1=$!
wait $P1
#numactl --membind=1 --physcpubind=48 ./wrk/wrk -t 1 -c 32 -d 300s -L http://127.0.0.1:9090/1kb.bin
#numactl --membind=1 --physcpubind=48 ./wrk/wrk -t 1 -c 140 -d 300s -L http://127.0.0.1:80/1K
sleep 2
numactl --membind=1 --physcpubind=32 ./wrk/wrk -t 1 -c 96 -d 300s -L http://127.0.0.1:80/1K

docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)
docker build -t mynginx .

docker run --cpuset-cpus=0-3 -e NGINX_CORE=4 -td -p 80:80 --name nginxtest  mynginx:latest
P1=$!
wait $P1
sleep 2
#numactl --membind=1 --physcpubind=48-51 ./wrk/wrk -t 4 -c 128 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-35 ./wrk/wrk -t 4 -c 400 -d 300s -L http://127.0.0.1:80/1K

docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)
docker build -t mynginx .



docker run --cpuset-cpus=0-7 -e NGINX_CORE=8 -td -p 80:80 --name nginxtest  mynginx:latest
P1=$!
wait $P1
sleep 2
#numactl --membind=1 --physcpubind=48-55 ./wrk/wrk -t 8 -c 224 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-39 ./wrk/wrk -t 8 -c 800 -d 300s -L http://127.0.0.1:80/1K

docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)
docker build -t mynginx .


docker run --cpuset-cpus=0-15 -e NGINX_CORE=16 -td -p 80:80 --name nginxtest  mynginx:latest
P1=$!
wait $P1
sleep 2
#numactl --membind=1 --physcpubind=48-63 ./wrk/wrk -t 16 -c  -d 336s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-47 ./wrk/wrk -t 16 -c 1120 -d 300s -L http://127.0.0.1:80/1K

docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)
docker build -t mynginx .


docker run --cpuset-cpus=0-31 -e NGINX_CORE=32 -td -p 80:80 --name nginxtest  mynginx:latest
P1=$!
wait $P1
sleep 2
#numactl --membind=1 --physcpubind=48-79 ./wrk/wrk -t 32 -c 224 -d 300s -L http://127.0.0.1:9090/1kb.bin
numactl --membind=1 --physcpubind=32-63 ./wrk/wrk -t 32 -c 1152 -d 300s -L http://127.0.0.1:80/1K

docker image rm -f localhost/mynginx
docker stop nginxtest
docker rm -f $(docker ps -a -q)

