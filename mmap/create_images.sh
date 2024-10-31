#! /bin/bash

for i in {1..20};
do
dd if=/dev/pmem12 of=/mnt/pmem12/img_file${i} bs=1M count=20480
done
