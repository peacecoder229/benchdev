#!/bin/sh

rm -f /root/aep1.txt
rm -f /root/aep2.txt

killall -9 iostat
iostat -d nvme0n1 -mx | grep "Device" > /root/aep1.txt
iostat -d nvme1n1 -mx | grep "Device" > /root/aep2.txt


iostat -d nvme0n1 -mx 1 580  | grep "nvme0n1" >> /root/aep1.txt &
iostat -d nvme1n1 -mx 1 580 | grep "nvme1n1" >> /root/aep2.txt &

sleep 580
