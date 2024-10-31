#!/bin/bash

SPEC_OPTS=""

# Java options for Composite JVM
JAVA_OPTS="-Xmx12g -Xms12g -Xmn12g -XX:MaxPermSize -XX:+UseG1GC -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/tmp/gc.log -XX:ParallelGCThreads=56"
JAVA_OPTS="-server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15 -Xms29g -Xmx29g -Xmn27g -XX:ParallelGCThreads=28 -Xloggc:/tmp/gc.log -XX:+PrintGCDateStamps -XX:MaxPermSize"

# Optional arguments for the Composite mode (-l <num>, -p <file>, -skipReport, etc.)
MODE_ARGS=""

# Number of successive runs

function start_jbb() {
	pkill -9 java
	result=./COM-$PRESETSTEP
	
	mkdir $result
	cp -r config $result
	cd $result

	java $JAVA_OPTS $SPEC_OPTS -jar ../specjbb2015.jar -ikv -m COMPOSITE $MODE_ARGS 2>composite.log > composite.out &
	COMPOSITE_PID=$!
	echo "PID: $COMPOSITE_PID"
	sleep 3
	wait $COMPOSITE_PID 
	cd -
}
export ADDTXTOUT=200

export PRESETSTEP=2000
start_jbb


export PRESETSTEP=5000
start_jbb


export PRESETSTEP=10000
start_jbb
