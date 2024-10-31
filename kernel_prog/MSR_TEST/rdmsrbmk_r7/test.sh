#!/bin/bash


#NPOINTS=250
#NITER=$NPOINTS/250

#10 iter = 10k points
#100 iter = 100k points
#1000 iter = 1M points
NITER=100   #default 100
echo Running for $NITER iterations. 

./clean.sh #somewhat redundant  
make clean
make

rm -Rf results/*
rm -Rf results.tar.bz2
mkdir results
mkdir results/raw_data

if [ -e "testmsr.ko" ] 
then
	echo Kernel module successfully compiled.
else
	echo Kernel module failed to build!
	echo Please notify Andrew!
	exit 1;
fi

CNT=0
while [ $CNT -lt $NITER ]; do
	numactl -m0 nice -n -20 /usr/bin/taskset -c 1 dmesg --clear
	numactl -m0 nice -n -20 /usr/bin/taskset -c 1 insmod testmsr.ko 
	#sleep 1;
	numactl -m0 nice -n -20 /usr/bin/taskset -c 1 dmesg &> results/output$CNT.txt
	numactl -m0 nice -n -20 /usr/bin/taskset -c 1 rmmod testmsr
	let CNT=CNT+1
done


echo Done!
echo Please email results.tar.bz2 to Andrew!

