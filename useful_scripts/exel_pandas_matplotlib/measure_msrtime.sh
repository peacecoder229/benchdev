#!/bin/bash

time_start=$(expr `date +%s%N` / 1000)
for i in {1..100000}; do rdmsr 0x199 ; done
time_end=$(expr `date +%s%N` / 1000)
avg_time=$(($(($time_end - $time_start))/100000))

echo $avg_time
