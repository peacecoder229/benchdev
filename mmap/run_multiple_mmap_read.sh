!#/bin/bash

for i in {0..17}
do
taskset -c $i ./mm_copy_in_loop /pnpdata/mmap/img_file 1024000000 4096 10000000 &
done
