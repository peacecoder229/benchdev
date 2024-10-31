#!/bin/bash

###############################################################################
## Sample script for running SPECjbb2015 in Composite mode.
## 
## This sample script demonstrates launching the Controller, TxInjector and 
## Backend in a single JVM.
###############################################################################

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Benchmark options (-Dproperty=value to override the default and property file value)
# Please add -Dspecjbb.controller.host=$CTRL_IP (this host IP) and -Dspecjbb.time.server=true
# when launching Composite mode in virtual environment with Time Server located on the native host.

# Java options for Composite JVM

CONF_TYPE=$1
CONF_IR=$2
CONF_DURATION=$3
CORE_NUM=$4
PORT=$5
tag=$6
#GC=$((${CORE_NUM}-4))
#GC=$(CORE_NUM)
TIER1=$((${CORE_NUM}*6))
TIER2=$((${CORE_NUM}*2))
TIER3=${CORE_NUM}
heapmax=$((${CORE_NUM}*2))
heapmn=$(( $heapmax-2 ))
echo $$
echo $TIER1 $TIER2 $TIER3 $CORE_NUM $test_cores






#JAVA_OPTS="-Xmx29g -Xms29g -Xmn27g"

JAVA_OPTS="-Xmx${heapmax}g -Xms${heapmax}g -Xmn${heapmn}g -XX:+UseParallelOldGC -XX:ParallelGCThreads=$CORE_NUM -XX:SurvivorRatio=30 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15"

rm -f config/specjbb2015.props

echo "specjbb.controller.type=${CONF_TYPE}" >> config/specjbb2015.props
echo "specjbb.controller.preset.ir=${CONF_IR}" >> config/specjbb2015.props
echo "specjbb.controller.preset.duration=${CONF_DURATION}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier1=${TIER1}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier2=${TIER2}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier3=${TIER3}" >> config/specjbb2015.props
echo "specjbb.controller.port=${PORT}" >> config/specjbb2015.props

# Optional arguments for the Composite mode (-l <num>, -p <file>, -skipReport, etc.)

# Number of successive runs
NUM_OF_RUNS=1

###############################################################################
# This benchmark requires a JDK7 compliant Java VM.  If such a JVM is not on
# your path already you must set the JAVA environment variable to point to
# where the 'java' executable can be found.
#
# If you are using a JDK9 Java VM, see the FAQ at:
#                       http://spec.org/jbb2015/docs/faq.html
###############################################################################

JAVA=java
sync; echo 3>       /proc/sys/vm/drop_caches

which $JAVA > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Could not find a 'java' executable. Please set the JAVA environment variable or update the PATH."
    exit 1
fi

for ((n=1; $n<=$NUM_OF_RUNS; n=$n+1)); do

  # Create result directory                
  timestamp=c${tag}_IR${CONF_IR}-$(date '+%y-%m-%d_%H%M%S')
  result=./result/$timestamp
  mkdir -p $result

  # Copy current config to the result directory
  cp -r config $result

  cd $result

  echo "Run $n: $timestamp"
  echo "Launching SPECjbb2015 in Composite mode..."
  echo

  echo "Start Composite JVM"
  $JAVA $JAVA_OPTS $SPEC_OPTS -jar ../../specjbb2015.jar -m COMPOSITE $MODE_ARGS 2>composite.log > composite.out &

    COMPOSITE_PID=$!
    echo "Composite JVM PID = $COMPOSITE_PID"

  sleep 3

  echo
  echo "SPECjbb2015 is running..."
  echo "Please monitor $result/controller.out for progress"

  wait $COMPOSITE_PID
  echo
  echo "Composite JVM has stopped"

  echo "SPECjbb2015 has finished"

  median=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $2} END {print SUM/NR}')
   p90=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $4} END {print SUM/NR}')
   p95=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $5} END {print SUM/NR}')

         file="specjbb_comp_${CORE_NUM}_${CONF_IR}.log"
	 echo "COMP_CC COMP_IR median p90 p95" >> ${file}
	 echo "${CORE_NUM} ${CONF_IR} ${median} ${p90} ${p95}" >> ${file}
	 cp -f $file /Nizar/cpu2017/


  echo

 cd ..

done

exit 0
