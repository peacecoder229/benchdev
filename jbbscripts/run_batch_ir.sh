#!/bin/bash

SPEC_OPTS=""

# Java options for Composite JVM
JAVA_OPTS="-Xmx12g -Xms12g -Xmn12g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

# Optional arguments for the Composite mode (-l <num>, -p <file>, -skipReport, etc.)
MODE_ARGS=""

# Number of successive runs

function start_jbb() {
	pkill -9 java
	result=./IR-2000_$1
	
	mkdir $result
	cp -r config $result

	sed "s/specjbb.controller.preset.ir=8000/specjbb.controller.preset.ir=$1/g" config/specjbb2015.props > $result/config/specjbb2015.props

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

for i in `seq 10`
do
	start_jbb ${i}000
done


