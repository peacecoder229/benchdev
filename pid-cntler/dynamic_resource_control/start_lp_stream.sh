#!/bin/bash
	LP_CPUSET=$2
        count=$1
        echo "==Start $count streams=="
        for i in `seq 1 $count`
        do
                docker run --cpuset-cpus=$LP_CPUSET -d --name LP-stream-$i stream:loop
        done


