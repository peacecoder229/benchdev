#!/bin/bash

###############################################################################
# Sample script for running SPECjbb2015 in Distributed mode.
#
# This sample script demonstrates launching the Backend(s) on the SUT host,
# ready to communicate with the Controller and TxInjector(s) on an auxiliary
# host.
#
###############################################################################

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Number of Groups (TxInjectors mapped to Backend) to expect
GROUP_COUNT=1

# Controller host IP to provide connection between agents
CTRL_IP=

# Benchmark options for Backend (-Dproperty=value to override the default and property file value)
SPEC_OPTS_BE="-Dspecjbb.controller.host=$CTRL_IP"

# Java options for Backend JVM
JAVA_OPTS_BE=""

# Optional arguments for Backend mode (-d <distribution>, -p <file>, etc.)
MODE_ARGS_BE=""

# Only update these two fields below in case of running Backends on multiple SUTs.
# For example, if one plan to run 8 Groups on 2 SUTs then:
#     first SUT setting:  BE_COUNT_START=1 BE_COUNT_END=4
#     second SUT setting: BE_COUNT_START=5 BE_COUNT_END=8

BE_COUNT_START=1
BE_COUNT_END=$GROUP_COUNT

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
    echo "ERROR: Failed to ping Controller host: $CTRL_IP"
    exit 1
fi

echo "Controller IP is set to: $CTRL_IP"
echo

echo "Launching SPECjbb2015 in Distributed mode..."
echo

echo "Launching Backend JVM(s) on SUT..."

for ((gnum=$BE_COUNT_START; $gnum<=$BE_COUNT_END; gnum=$gnum+1)); do

    GROUPID=Group$gnum
    echo -e "\nStarting JVMs from $GROUPID:"

    JVMID=beJVM
    BE_NAME=$GROUPID.Backend.$JVMID

    echo "    Start $BE_NAME"
    $JAVA $JAVA_OPTS_BE $SPEC_OPTS_BE -jar specjbb2015.jar -m BACKEND -G=$GROUPID -J=$JVMID $MODE_ARGS_BE > $BE_NAME.log 2>&1 &
    echo -e "\t$BE_NAME PID = $!"
    sleep 1

done

echo
echo "SPECjbb2015 is running..."
echo "Please launch Controller and TxInjector JVM(s) on Controller host $CTRL_IP (if not already launched) and monitor Controller output for progress"
echo
exit 0
