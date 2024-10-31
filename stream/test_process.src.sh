#!/bin/bash 

# This is the helpers for RDT issue test.
#

function baseline(){
	# only run hp, without any configurations

	echo "============BASE LINE=============="
	WORK_PATH="$PORJ/baseline"
	prepare
	
	start_pqos_monitor
	start_emon
	start_hp	
	stop_emon
	stop_pqos_monitor 
}

function noisy(){
	# hp + lp, without configuration

	echo "============BASE LINE + NOISY =============="
	WORK_PATH="$PORJ/noisy"
	prepare
	
	start_pqos_monitor
	
	start_lp & 
	start_emon
	start_hp
	stop_emon	
	stop_lp

	stop_pqos_monitor 
}


function rdt(){
	echo "============BASE LINE + NOISY + CAT =============="
	WORK_PATH="$PORJ/noisy_with_RDT"
	prepare
	
	set_llc_mba $HP_WAY $LP_WAY 100 100
	start_pqos_monitor

	start_lp &
	start_emon
	start_hp
	stop_emon
	stop_lp
	
	stop_pqos_monitor 
	
}

function mba_only(){
	# only MBA, no CAT

	if [ $PLAFORM = "skx" ]
	then
		
		echo "============BASE LINE + NOISY + MBA =============="
		WORK_PATH="$PORJ/noisy_with_MBA"
		prepare
	
		set_llc_mba $TOTAL_LLC_WAYS $TOTAL_LLC_WAYS $HP_MBA $LP_MBA
		start_pqos_monitor
	
		start_lp &
		start_emon
		start_hp 
		stop_lp
		stop_emon
		stop_pqos_monitor 
	fi
	
}


function mba(){
	# CAT + MBA

	if [ $PLAFORM = "skx" ]
	then
		
		echo "============BASE LINE + NOISY + CAT + MBA =============="
		WORK_PATH="$PORJ/noisy_with_RDT_MBA"
		prepare
	
		set_llc_mba $HP_WAY $LP_WAY $HP_MBA $LP_MBA
		start_pqos_monitor
	
		start_lp &
		start_emon
		start_hp 
		stop_emon
		stop_pqos_monitor 
	fi
	
}

function single_test(){

		echo "============ Single Test =============="
		WORK_PATH="$PORJ"
		prepare

		set_llc_mba $HP_WAY $LP_WAY $HP_MBA $LP_MBA
		start_pqos_monitor

		start_lp &
		start_emon
		start_hp
		stop_emon
		stop_pqos_monitor


}

function exec_test(){
	# combind all test cases

	mkdir -p $PORJ
	hostname >> $PORJ/cmd.txt
	echo $CMD >> $PORJ/cmd.txt
	date >> $PORJ/cmd.txt

	echo "============BASE LINE=============="
	WORK_PATH="$PORJ/baseline"
	prepare
	
	start_pqos_monitor
	start_emon
	start_hp	
	stop_emon
	stop_pqos_monitor 
	
	echo "============BASE LINE + NOISY =============="
	WORK_PATH="$PORJ/noisy"
	prepare
	
	start_pqos_monitor
	
	start_lp & 
	start_emon
	start_hp
	stop_emon
	stop_lp

	stop_pqos_monitor 
	
	echo "============BASE LINE + NOISY + CAT =============="
	WORK_PATH="$PORJ/noisy_with_RDT"
	prepare
	
	set_llc_mba $HP_WAY $LP_WAY 100 100
	start_pqos_monitor

	start_lp &
	start_emon
	start_hp
	stop_emon
 	stop_lp
	
	stop_pqos_monitor 
	
	if [ $PLAFORM = "skx" ]
	then
		
		echo "============BASE LINE + NOISY + CAT + MBA =============="
		WORK_PATH="$PORJ/noisy_with_RDT_MBA"
		prepare
	
		set_llc_mba $HP_WAY $LP_WAY $HP_MBA $LP_MBA
		start_pqos_monitor
	
		start_lp &
		start_emon
		start_hp 
		stop_emon
		stop_pqos_monitor 
		stop_lp
	fi
	pqos -R
}

function display_score(){
	# results summarization

	old=`pwd`
	
	cd $PORJ
	for path in `ls`
	do 
		echo ++++++++++${path}++++++++ 
		cat $path/score.txt
	done
    
	cd $old
}	
