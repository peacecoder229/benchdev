source ./test_process.inc.sh 
source ./emon.inc.sh


HP_CORES=24-35,72-83
LP_CORES=36-47,84-95

DEFAULT_CAT=0x7ff

./hwpdesire.sh -f 2100000

ROOT=`date +WW%W.%w-%H%M`

initial_settings

for hp in $( cat ?p_wl.txt | sort | uniq )
do
	baseline $hp $ROOT/$hp
done
