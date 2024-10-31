#!/bin/bash

###############################################################################
# Sample script for running SPECjbb2015 Time Server.
#
# This sample script demonstrates launching the Time Server on the native host, 
# ready to communicate with Controller launched on the virtual SUT.
#
###############################################################################

# Launch command: java [options] -jar specjbb2015.jar -m TIMESERVER [argument] [value] ...

# Controller host IP to provide connection between Time Server and Controller
# IP where Multi Controller JVM or Composite JVM is going to be launched
CTRL_IP=

# Benchmark options for Time Server 
# Please use -Dproperty=value to override the default and property file value
SPEC_OPTS="-Dspecjbb.controller.host=$CTRL_IP"

# Java options for Time Server
JAVA_OPTS=""

# Optional arguments for Time Server mode
# For more info please use: java -jar specjbb2015.jar -m <mode> -h
MODE_ARGS=""

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

echo "Launching SPECjbb2015 Time Server..."
$JAVA $JAVA_OPTS $SPEC_OPTS -jar specjbb2015.jar -m TIMESERVER $MODE_ARGS 2>timeserver.log > timeserver.out &

TS_PID=$!
echo "TimeServer PID = $TS_PID"

echo
echo "TimeServer is running..."
echo
echo "Please launch Multi Controller or Composite JVM on $CTRL_IP (if not already launched) and monitor its output for progress"

wait $TS_PID
echo
echo "Time Server has stopped"

exit 0
