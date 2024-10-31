#!/bin/bash

# Changed AEP way assignment to LP ways

source /pnpdata/skx_issue_tools/scripts/test.src.sh
source /pnpdata/skx_issue_tools/scripts/test_process.src.sh
heap="25"
ir="8000"
cc="4"
cpu="18-19,46-47"

		printf "%s is IR and %s is corec and %s is cpus %s  is heap\n" "$ir" "$cc" "$cpu" "$heap"
		HP_INSTANCES=$cc
		HP_CPUSET=$cpu
		WORK_PATH="singlespecJBB2015"
		result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${cpu}_HEAP${heap}"
		prepare
		#taskset -c 28 pqos -r -i 5 -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &
		many_specjbb2015_multi  $ir $heap $cpu &
		

heap="25"
ir="8000"
cc="4"
cpu="20-21,48-49"

		HP_INSTANCES=$cc
                HP_CPUSET=$cpu
                WORK_PATH="singlespecJBB2015"
                result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${cpu}_HEAP${heap}"
                #taskset -c 28 pqos -r -i 5 -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &
                many_specjbb2015_multi  $ir $heap $cpu &










heap="25"
ir="8000"
cc="4"
cpu="22-23,50-51"

                HP_INSTANCES=$cc
                HP_CPUSET=$cpu
                WORK_PATH="singlespecJBB2015"
                result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${cpu}_HEAP${heap}"
                #taskset -c 28 pqos -r -i 5 -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &
                many_specjbb2015_multi  $ir $heap $cpu &




		#pkill -9 pqos

heap="25"
ir="8000"
cc="4"
cpu="24-25,52-53"

                HP_INSTANCES=$cc
                HP_CPUSET=$cpu
                WORK_PATH="singlespecJBB2015"
                result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${cpu}_HEAP${heap}"
                #taskset -c 28 pqos -r -i 5 -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &
                many_specjbb2015_multi  $ir $heap $cpu &




		#pkill -9 pqos
heap="25"
ir="8000"
cc="4"
cpu="26-27,54-55"

		printf "%s is IR and %s is corec and %s is cpus %s  is heap\n" "$ir" "$cc" "$cpu" "$heap"
		HP_INSTANCES=$cc
		HP_CPUSET=$cpu
		WORK_PATH="singlespecJBB2015"
		result_path="$WORK_PATH/HP_specjbb2015_IR${ir}_core${cpu}_HEAP${heap}"
		#prepare
		#taskset -c 28 pqos -r -i 5 -m "all:[$HP_CPUSET]"  -o $result_path/rdt.out &
		many_specjbb2015_multi  $ir $heap $cpu &
		











