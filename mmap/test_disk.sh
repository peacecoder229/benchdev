#! /bin/bash


	taskset -c 2 ./test_mmap_copy /pnpdata/mmap/img_file 1024000000 $1 &

