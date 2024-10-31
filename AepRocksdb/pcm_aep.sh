#!/bin/sh
rm -f ./pcm.log
./pcm-memory.x -ddr-t|grep NODE >> ./pcm.log &
sleep 850
killall -9 pcm-memory.x


