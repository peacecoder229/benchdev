#! /bin/bash

while :
do
	taskset -c 2 ./mm_map_blkrd /mnt/pmem12/img_file1 1024000000 $1 &
	taskset -c 3 ./mm_map_blkrd /mnt/pmem12/img_file2 1024000000 $1 &
	taskset -c 4 ./mm_map_blkrd /mnt/pmem12/img_file3 1024000000 $1 &
	taskset -c 5 ./mm_map_blkrd /mnt/pmem12/img_file4 1024000000 $1 &
	taskset -c 6 ./mm_map_blkrd /mnt/pmem12/img_file5 1024000000 $1 &
	taskset -c 7 ./mm_map_blkrd /mnt/pmem12/img_file6 1024000000 $1 

done

