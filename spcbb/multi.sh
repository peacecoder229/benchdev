#!/bin/bash

CONF_TYPE=$1
CONF_IR=$2
CONF_DURATION=$3
CORE_NUM=$4
PORT=$5
tag=$6
heapmax=$((${CORE_NUM}*2))
heapmn=$(( $heapmax-2 ))
#GC=$((${CORE_NUM}-4))
#GC=$(CORE_NUM)
TIER1=$((${CORE_NUM}*6))
TIER2=$((${CORE_NUM}*2))
TIER3=${CORE_NUM}

echo $$
echo $TIER1 $TIER2 $TIER3 $CORE_NUM $test_cores



# pkill -9 java

rm -f config/specjbb2015.props

echo "specjbb.controller.type=${CONF_TYPE}" >> config/specjbb2015.props
echo "specjbb.controller.preset.ir=${CONF_IR}" >> config/specjbb2015.props
echo "specjbb.controller.preset.duration=${CONF_DURATION}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier1=${TIER1}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier2=${TIER2}" >> config/specjbb2015.props
echo "specjbb.forkjoin.workers.Tier3=${TIER3}" >> config/specjbb2015.props
echo "specjbb.controller.port=${PORT}" >> config/specjbb2015.props


###############################################################################
# Sample script for running SPECjbb2015 in MultiJVM mode.
# 
# This sample script demonstrates running the Controller, TxInjector(s) and 
# Backend(s) in separate JVMs on the same server.
###############################################################################

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Number of Groups (TxInjectors mapped to Backend) to expect
GROUP_COUNT=1

# Number of TxInjector JVMs to expect in each Group
TI_JVM_COUNT=1

# Benchmark options for Controller / TxInjector JVM / Backend
# Please use -Dproperty=value to override the default and property file value
# Please add -Dspecjbb.controller.host=$CTRL_IP (this host IP) to the benchmark options for the all components
# and -Dspecjbb.time.server=true to the benchmark options for Controller 
# when launching MultiJVM mode in virtual environment with Time Server located on the native host.
SPEC_OPTS_C="-Dspecjbb.group.count=$GROUP_COUNT -Dspecjbb.txi.pergroup.count=$TI_JVM_COUNT"
SPEC_OPTS_TI=""
SPEC_OPTS_BE=""

# Java options for Controller / TxInjector / Backend JVM
JAVA_OPTS_COMP="-Xmx${heapmax}g -Xms${heapmax}g -Xmn${heapmn}g -XX:+UseParallelOldGC -XX:ParallelGCThreads=$CORE_NUM -XX:SurvivorRatio=30 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15"
JAVA_OPTS_C="-showversion -Xmn1536m -Xms2g -Xmx2g"
JAVA_OPTS_TI="-showversion -Xmn1536m -Xms2g -Xmx2g"
JAVA_OPTS_BE=$JAVA_OPTS_COMP

# Optional arguments for multiController / TxInjector / Backend mode 
# For more info please use: java -jar specjbb2015.jar -m <mode> -h
MODE_ARGS_C=""
MODE_ARGS_TI=""
MODE_ARGS_BE=""

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

#JAVA=/usr/lib/jvm/bin/java
JAVA=/usr/bin/java
sync; echo 3 >  /proc/sys/vm/drop_caches

which $JAVA > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Could not find a 'java' executable. Please set the JAVA environment variable or update the PATH."
    exit 1
fi

for ((n=1; $n<=$NUM_OF_RUNS; n=$n+1)); do

  # Create result directory                modified result directory not to contained any timestamps
  #timestamp=m${tag}_IR${CONF_IR}-$(date '+%y-%m-%d_%H%M%S')
  timestamp=m${tag}_IR${CONF_IR}
  result=result/$timestamp
  mkdir -p $result

  # Copy current config to the result directory
  cp -r config $result

  cd $result

  echo "Run $n: $timestamp"
  echo "Launching SPECjbb2015 in MultiJVM mode..."
  echo

  echo "Start Controller JVM"
  $JAVA $JAVA_OPTS_C $SPEC_OPTS_C -jar ../../specjbb2015.jar -m MULTICONTROLLER $MODE_ARGS_C 2>controller.log > controller.out &

  CTRL_PID=$!
  echo "Controller PID = $CTRL_PID"

  sleep 5

  for ((gnum=1; $gnum<$GROUP_COUNT+1; gnum=$gnum+1)); do
    
    rand=$(tr -cd 0-9 </dev/urandom | head -c 2)

    #GROUPID=Group$gnum
    GROUPID=Group$rand
    echo -e "\nStarting JVMs from $GROUPID:"

    for ((jnum=1; $jnum<$TI_JVM_COUNT+1; jnum=$jnum+1)); do

        JVMID=txiJVM$jnum
        TI_NAME=$GROUPID.TxInjector.$JVMID

        echo "    Start $TI_NAME"
        $JAVA $JAVA_OPTS_TI $SPEC_OPTS_TI -jar ../../specjbb2015.jar -m TXINJECTOR -G=$GROUPID -J=$JVMID $MODE_ARGS_TI > $TI_NAME.log 2>&1 &
        echo -e "\t$TI_NAME PID = $!"
        sleep 1
    done

    JVMID=beJVM$rand
    BE_NAME=$GROUPID.Backend.$JVMID

    echo "    Start $BE_NAME"
    $JAVA $JAVA_OPTS_BE $SPEC_OPTS_BE -jar ../../specjbb2015.jar -m BACKEND -G=$GROUPID -J=$JVMID $MODE_ARGS_BE > $BE_NAME.log 2>&1 &
    echo -e "\t$BE_NAME PID = $!"
    sleep 1

  done

  echo
  echo "SPECjbb2015 is running..."
  echo "Please monitor $result/controller.out for progress"

  wait $CTRL_PID
  echo
  echo "Controller has stopped"

  echo "SPECjbb2015 has finished"

#    median=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $2} END {print SUM/NR}')
#    p90=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $4} END {print SUM/NR}')
#    p95=$(cat result/specjbb2015-*/report-*/data/rt-curve/specjbb2015*-overall-throughput-rt.txt | grep  "^[0-9]" | awk -F\; '{SUM += $5} END {print SUM/NR}')
#    file="specjbb_${CORE_NUM}_${CONF_IR}.log"
#    echo "CORE_NUM CONF_IR median p90 p95" >> ${file}
#    echo "${CORE_NUM} ${CONF_IR} ${median} ${p90} ${p95}" >> ${file}
#    cp -f $file /root/QoS_scripts
#
#  echo
  
  cd ..

done

exit 0
