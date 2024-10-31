#!/bin/bash

###############################################################################
## Sample script for running SPECjbb2015 in Composite mode.
## 
## This sample script demonstrates launching the Controller, TxInjector and 
## Backend in a single JVM.
###############################################################################

export PRESETSTEP=2000
export ADDTXTOUT=200

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Benchmark options (-Dproperty=value to override the default and property file value)
# Please add -Dspecjbb.controller.host=$CTRL_IP (this host IP) and -Dspecjbb.time.server=true
# when launching Composite mode in virtual environment with Time Server located on the native host.
SPEC_OPTS=""

# Java options for Composite JVM
JAVA_OPTS=""

# Optional arguments for the Composite mode (-l <num>, -p <file>, -skipReport, etc.)
MODE_ARGS=""

JAVA=java

pkill -9 $JAVA
           
timestamp=$(date '+%y-%m-%d_%H%M%S')
result=./$timestamp
mkdir $result

cp -r config $result

cd $result

echo "Launching SPECjbb2015 in Composite mode..."
echo

$JAVA $JAVA_OPTS $SPEC_OPTS -jar ../specjbb2015.jar -ikv -m COMPOSITE $MODE_ARGS 2>composite.log > composite.out &

COMPOSITE_PID=$!

sleep 3

# tail -s 0.5 -f composite.out | grep TotalPurchase &
python ../results_formatter.py -w "tail -s 0.5 -f `pwd`/composite.out" -p specjbb2015 &

wait $COMPOSITE_PID
echo
echo "Composite JVM has stopped"

echo "SPECjbb2015 has finished"
echo

cd ..
rm -rf $result

exit 0
