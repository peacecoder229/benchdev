make clean && make
rm -rf results
mkdir -p results
numactl -m0 nice -n -20 /usr/bin/taskset -c 1 dmesg --clear
numactl -m0 nice -n -20 /usr/bin/taskset -c 1 insmod readctr.ko
sleep 10
numactl -m0 nice -n -20 /usr/bin/taskset -c 1 dmesg &> results/output.txt
numactl -m0 nice -n -20 /usr/bin/taskset -c 1 rmmod readctr

