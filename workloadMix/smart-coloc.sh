#!/bin/bash 

source ./test_process.inc.sh 
# enable emon here
#source ./emon.inc.sh

HP_CORES=0-13
LP_CORES=14-27

HP_INSTANCE=14
LP_INSTANCE=14


DEFAULT_CAT=0x7ff

./hwpdesire.sh -f 2100000

function read_hp_score()
{
	p=$1
	cat `find $p -name "summary.txt" ` | awk '{print $6}'

#	echo 12346.2 # enable this line for debugging 
}

function read_hp_after_finish()
{
	hp=$1
	lp=$2
	path=$3
	
	start_workloads $1 $2 $3 # disable this line for debugging.
	
#	read_hp_score $3
}

function smart_colocation()
{	
	ROOT=`date +WW%W.%w-%H%M`-SMART
	hp_workload="specjbb"
	lp_workload="bwaves"

	taget=0.85

	initial_settings
	read_hp_after_finish $hp_workload "empty" $ROOT/hp
	score=$( read_hp_score $ROOT/hp )


	target_score=$( echo "$score * $taget" | bc )
        echo "======target==$target_score======"

        LOOP=1
# 	enable_HWDRC 

	while [ $LOOP -lt 7 ]
	do
		echo "======Start loop $LOOP======"
		read_hp_after_finish $hp_workload $lp_workload $ROOT/LOOP-$LOOP
		score=$( read_hp_score $ROOT/LOOP-$LOOP )
		
		if [  $( echo "$target_score < $score" | bc ) -eq 1  ]
		then
			LOOP=100
			echo LP core: $LP_INSTANCE, HP score: $score
		else
			LP_INSTANCE=$(( $LP_INSTANCE - 2 ))
			LOOP=$(( $LOOP + 1 ))
		fi

	done

	set_swdrc >> swdrc.log
	echo "======HWDRC enabled======"

	LOOP=1
	while [ $LOOP -lt 7 ]
	do
		echo "======Start loop $LOOP======"
		read_hp_after_finish $hp_workload $lp_workload $ROOT/SWDRC-$LOOP
		score=$( read_hp_score $ROOT/SWDRC-$LOOP )
		

		if [  $( echo "$target_score < $score" | bc ) -eq 1  ]
		then
			LOOP=100
			echo LP core: $LP_INSTANCE, HP score: $score
		else
			LP_INSTANCE=$(( $LP_INSTANCE - 2 ))
			LOOP=$(( $LOOP + 1 ))
		fi

	done


#	while [ $taget -gt $(read_hp_after_finish $hp_workload $lp_workload $ROOT/$LOOP) ]
#	do
#		LP_INSTANCE=$(( $LP_INSTANCE - 2 ))
#		LOOP=$(( $LOOP + 1 ))
#	done
	

}

smart_colocation
