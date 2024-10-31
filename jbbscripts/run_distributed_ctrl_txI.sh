#!/bin/bash

###############################################################################
# Sample script for running SPECjbb2015 in Distributed mode.
#
# This sample script demonstrates launching the Controller and TxInjector(s)
# on an auxiliary host, ready to communicate with Backend(s) launched on a
# separate SUT host.
#
###############################################################################

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Number of Groups (TxInjectors mapped to Backend) to expect
GROUP_COUNT=1

# How many TxInjector JVMs to expect in each Group
TI_JVM_COUNT=1

# Controller host IP to provide connection between agents
# This host IP where Controller is going to be launched
CTRL_IP=

# Benchmark options for Controller / TxInjector 
# Please use -Dproperty=value to override the default and property file value
SPEC_OPTS_C="-Dspecjbb.controller.host=$CTRL_IP -Dspecjbb.group.count=$GROUP_COUNT -Dspecjbb.txi.pergroup.count=$TI_JVM_COUNT"
SPEC_OPTS_TI="-Dspecjbb.controller.host=$CTRL_IP"

# Java options for Controller / TxInjector JVM
JAVA_OPTS_C=""
JAVA_OPTS_TI=""

# Optional arguments for distController / TxInjector mode
# For more info please use: java -jar specjbb2015.jar -m <mode> -h
MODE_ARGS_C=""
MODE_ARGS_TI=""

###############################################################################
# This benchmark requires a JDK7 compliant Java VM.  If such a JVM is not on
# your path already you must set the JAVA environment variable to point to
# where the 'java' executable can be found.
#
# If you are using a JDK9 Java VM, see the FAQ at:
#                       http://spec.org/jbb2015/docs/faq.html
###############################################################################

JAVA=java

which $JAVA > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Could not find a 'java' executable. Please set the JAVA environment variable or update the PATH."
    exit 1
fi

ping -c 1 $CTRL_IP > /dev/null 2>&1
if [ "$?" -ne 0 ]; then
    echo "ERROR: Please define CTRL_IP as this host IP"
    exit 1
fi

echo "Controller IP (this host IP) is set to: $CTRL_IP"
echo

# Create result directory
timestamp=$(date '+%y-%m-%d_%H%M%S')
result=./$timestamp
mkdir $result

# Copy current config to the result directory
cp -r config $result

cd $result

echo "Run: $timestamp"
echo "Launching SPECjbb2015 in Distributed mode..."
echo

echo "Start Controller JVM"
$JAVA $JAVA_OPTS_C $SPEC_OPTS_C -jar ../specjbb2015.jar -m DISTCONTROLLER $MODE_ARGS_C 2>controller.log > controller.out &

CTRL_PID=$!
echo "Controller PID = $CTRL_PID"

sleep 3

for ((gnum=1; $gnum<$GROUP_COUNT+1; gnum=$gnum+1)); do

    GROUPID=Group$gnum
    echo -e "\nStarting JVMs from $GROUPID:"

    for ((jnum=1; $jnum<$TI_JVM_COUNT+1; jnum=$jnum+1)); do

        JVMID=txiJVM$jnum
        TI_NAME=$GROUPID.TxInjector.$JVMID

        echo "    Start $TI_NAME"
        $JAVA $JAVA_OPTS_TI $SPEC_OPTS_TI -jar ../specjbb2015.jar -m TXINJECTOR -G=$GROUPID -J=$JVMID $MODE_ARGS_TI > $TI_NAME.log 2>&1 &
        echo -e "\t$TI_NAME PID = $!"
        sleep 1
    done
done

echo
echo "Controller and TxInjector JVMs are running..."
echo
echo "Please launch Backend JVM(s) on SUT (if not already launched) and monitor $result/controller.out for progress"

wait $CTRL_PID
echo
echo "Controller has stopped"

echo "SPECjbb2015 has finished"
echo

cd ..

exit 0
