# To build the docker
echo off > /sys/devices/system/cpu/smt/control

docker build -t mynginx -f Dockerfile


# To run the nginx with the wrk in the compiled container use the following as an example

docker run --cpuset-cpus=0-24 -td -p 80:80 mynginx:latest

# To test, you can launch the wrk as follows

../baremetal/start-wrk-appstatdata.sh 24-47 24 12000 120000 4kb.bin 80 0



