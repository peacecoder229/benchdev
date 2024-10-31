#!/bin/bash

#################################################################################
# Sample script for running SPECjbb2015 reporter with different level of details
#
# Usage:
#
#    run_reporter.bat <binary log file name> <level of report details>
#
# Examples:
#
#     1)  run_reporter.sh specjbb2015-D-20150111-00001.data.gz 3
#     2)  run_reporter.sh /home/users/specjbb2015/specjbb2015-C-20150128-00001.data.gz 2
#
#################################################################################

# Launch command: java [options] -jar specjbb2015.jar [argument] [value] ...

# Java options for Reporter JVM
JAVA_OPTS=""

#################################################################################
# This benchmark requires a JDK7 compliant Java VM. If such a JVM is not on
# your path already you must set the JAVA environment variable to point to
# where the 'java' executable can be found.
#
# If you are using a JDK9 Java VM, see the FAQ at:
#                       http://spec.org/jbb2015/docs/faq.html
#################################################################################

JAVA=java

which $JAVA > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Could not find a 'java' executable. Please set the JAVA environment variable or update the PATH"
    exit 1
fi

echo "Run command: ./run_reporter.sh <binary_log_file> <report_details_level>"
echo
echo "Binary log file name: $1"
echo "Report details level: $2"

if [ ! -e "$1" ]; then
    echo "ERROR: No such file $1"
    exit 1
fi

echo
echo "Running SPECjbb2015 reporter..."
$JAVA $JAVA_OPTS -jar specjbb2015.jar -m REPORTER -s $1 -l $2 > reporter.log 2>&1
# if config/SPECjbb2015.prop files not there in default location user must define -p <property file> on the above launch command line
echo "Reporter has finished"

exit 0
