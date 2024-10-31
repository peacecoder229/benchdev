#! /bin/bash

while :
do
	taskset -c 2 ./mm_map_blkrd /mnt/pmem12/img_file1 1024000000 $1 &
	taskset -c 3 ./mm_map_blkrd /mnt/pmem12/img_file1 1024000000 $1 

done

