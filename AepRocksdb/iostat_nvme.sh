#!/bin/sh

rm -f /root/nvme1.txt
rm -f /root/nvme2.txt

killall -9 iostat
iostat -d nvme0n1 -mx | grep "Device" > /root/nvme1.txt
iostat -d nvme1n1 -mx | grep "Device" > /root/nvme2.txt


iostat -d nvme0n1 -mx 1 580  | grep "nvme0n1" >> /root/nvme1.txt &
iostat -d nvme1n1 -mx 1 580 | grep "nvme1n1" >> /root/nvme2.txt &

sleep 580
