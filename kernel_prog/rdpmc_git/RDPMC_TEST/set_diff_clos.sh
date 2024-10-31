#!/bin/bash


NITER=22
CNT=0
while [ $CNT -lt $NITER ]; do
        /usr/bin/taskset -c $CNT wrmsr -p $CNT 0xc8f 0x0
        let CNT=CNT+1
done

NITER=66
CNT=44
while [ $CNT -lt $NITER ]; do
        /usr/bin/taskset -c $CNT wrmsr -p $CNT 0xc8f 0xF00000000
        let CNT=CNT+1
done

echo OS CPU 0:
rdmsr -p0 0xc8f 
echo OS CPU 44:
rdmsr -p44 0xc8f 



