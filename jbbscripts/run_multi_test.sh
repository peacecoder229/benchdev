#!/bin/bash

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
JAVA_OPTS_C=""
JAVA_OPTS_TI=""

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

JAVA=java

function run_spec(){
	# Create result directory                
	timestamp=RT-IR$1_HEAP$2
	result=./$timestamp
	mkdir $result

	# Copy current config to the result directory
	cp -r config $result
	sed "s/specjbb.controller.preset.ir=8000/specjbb.controller.preset.ir=$1/g" config/specjbb2015.props > $result/config/specjbb2015.props
	cd $result

	pkill -9 $JAVA

	# controller
	$JAVA -Xmn1536m -Xms2g -Xmx2g $SPEC_OPTS_C -jar ../specjbb2015.jar -ikv -m MULTICONTROLLER $MODE_ARGS_C 2>controller.log > controller.out &

	CTRL_PID=$!
	echo $CTRL_PID
	sleep 3

	GROUPID=Group$gnum
	JVMID=txiJVM$jnum
	TI_NAME=$GROUPID.TxInjector.$JVMID
	#Injector
	$JAVA -Xmn1536m -Xms2g -Xmx2g $SPEC_OPTS_TI -jar ../specjbb2015.jar -ikv -m TXINJECTOR -G=$GROUPID -J=$JVMID $MODE_ARGS_TI > $TI_NAME.log 2>&1 &
	sleep 1

	JVMID=beJVM
	BE_NAME=$GROUPID.Backend.$JVMID
	# Backend
	$JAVA $JAVA_OPTS_BE $SPEC_OPTS_BE -jar ../specjbb2015.jar -ikv -m BACKEND -G=$GROUPID -J=$JVMID $MODE_ARGS_BE > $BE_NAME.log 2>&1 &

	wait $CTRL_PID
	
	cd ..
}

export ADDTXTOUT=200

export PRESETSTEP=2000

JAVA_OPTS="-server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15 -XX:ParallelGCThreads=28 -Xloggc:./gc.log -XX:+PrintGCDateStamps -XX:MaxPermSize"

JAVA_OPTS_BE="-Xmx80g -Xms80g -Xmn80g ${JAVA_OPTS}"
for i in `seq 2 9`
do
	run_spec ${i}000 20
done

JAVA_OPTS_BE="-Xmx70g -Xms70g -Xmn70g ${JAVA_OPTS}"
for i in `seq 2 6`
do
	run_spec ${i}000 30
done

JAVA_OPTS_BE="-Xmx60g -Xms60g -Xmn60g ${JAVA_OPTS}"
for i in `seq 2 6`
do
	run_spec ${i}000 40
done
