#! /bin/bash

for i in {20..20};
do
max=$[$i+1]
k="1"
while [ $k  -lt $max ]
do
if [ $k == $i ]
then
	taskset -c $k ./mm_map_blkrd /mnt/pmem12/img_file${k} 21474836480 4096 >> /root/pmem/nopop/run_${i}.log 2>&1 

else

	taskset -c $k ./mm_map_blkrd /mnt/pmem12/img_file${k} 21474836480 4096 >> /root/pmem/nopop/run_${i}.log 2>&1 &
 
fi

k=$[$k+1]

done

done

