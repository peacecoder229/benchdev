#!/bin/bash


#NPOINTS=1000
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

if [ -e "rdmsrbmk.ko" ] 
then
	echo Kernel module successfully compiled.
else
	echo Kernel module failed to build!
	echo Please notify Andrew!
	exit 1;
fi

CNT=0
while [ $CNT -lt $NITER ]; do
	numactl -m0 nice -n -20 /usr/bin/taskset -c 0 dmesg --clear
	numactl -m0 nice -n -20 /usr/bin/taskset -c 0 insmod rdmsrbmk.ko
	#sleep 1;
	numactl -m0 nice -n -20 /usr/bin/taskset -c 0 dmesg &> results/output$CNT.txt
	numactl -m0 nice -n -20 /usr/bin/taskset -c 0 rmmod rdmsrbmk
	let CNT=CNT+1
done

cat results/output*.txt | grep -e 'rdmsrbmk: Serialized: iter' &> results/rdtsc_ser.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xc8f=' &> results/rdmsr_0xc8f.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test(mode 0): 0xc8f' &> results/wrmsr_0xc8f_BOTH.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test(mode 1): 0xc8f' &> results/wrmsr_0xc8f_CLOS.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test(mode 2): 0xc8f' &> results/wrmsr_0xc8f_RMID.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test(mode 3): 0xc8f' &> results/wrmsr_0xc8f_STATIC.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xc8d=' &> results/rdmsr_0xc8d.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test: 0xc8d=' &> results/wrmsr_0xc8d.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xc8e=' &> results/rdmsr_0xc8e.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0x1a4=' &> results/rdmsr_0x1a4.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test: 0x1a4=' &> results/wrmsr_0x1a4.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xd50=' &> results/rdmsr_0xd50.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test: 0xd50=' &> results/wrmsr_0xd50.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xd70=' &> results/rdmsr_0xd70.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test: 0xd70=' &> results/wrmsr_0xd70.txt

cat results/output*.txt | grep -e 'rdmsrbmk: run_rdmsr_test: 0xc90=' &> results/rdmsr_0xc90.txt
cat results/output*.txt | grep -e 'rdmsrbmk: run_wrmsr_test: 0xc90=' &> results/wrmsr_0xc90.txt


mv results/output*.txt results/raw_data/
tar cvjf results.tar.bz2 results/*

echo Done!
echo Please email results.tar.bz2 to Andrew!

