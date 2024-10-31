#!/bin/sh
rm -f ./cpu_utility.log

turbostat --debug >> ./cpu_utility.log&
sleep 850
killall -9 turbostat
