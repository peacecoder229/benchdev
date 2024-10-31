
# Way allocation exclusive / inclusive switch
DUAL_SIDE=1
# MSB or LSB switch
MSB_LLC_WAY=1

function llc_mask(){
	# private function, only to convert llc ways to llc masks
	#$1 bit_ways
	#$2 lsb = 1, rsb = 0

	way=$1
	mask=$(((1<<${way})-1))

	if [ $2 = 1 -a $DUAL_SIDE = 1 ]
	then
		mask=$(((${mask}<<(${TOTAL_LLC_WAYS}-${way}))))
	fi
	echo "obase=16;${mask}" | bc
	# echo "obase=2;${mask}" | bc

}

HP_COS=4
LP_COS=5

function update_llc_mba(){
	# Set RDT allocation only
	#
	# $1 hp LLC way
	# $2 lp LLC way
	# $3 hp MBA
	# $4 lp MBA


	if [ $MSB_LLC_WAY = 0 ]
	then
		hp_mask=`llc_mask $1 0`
		lp_mask=`llc_mask $2 1`
	else
		hp_mask=`llc_mask $1 1`
		lp_mask=`llc_mask $2 0`
	fi

	hp_bw=$3
	lp_bw=$4
	
	pqos -R

	echo LLC/MBA: $hp_way $lp_way ${hp_bw} ${lp_bw}

	pqos -e "llc:${HP_COS}=0x${hp_mask}"
	pqos -e "llc:${LP_COS}=0x${lp_mask}"

	if [ $PLAFORM = 'skx' ]
	then
		pqos -e "mba:${HP_COS}=${hp_bw}"
		pqos -e "mba:${LP_COS}=${lp_bw}"
	fi
}

function set_llc_mba(){
	# set RDT COS and allocation
	#
	# $1 hp LLC way
	# $2 lp LLC way
	# $3 hp MBA
	# $4 lp MBA

	update_llc_mba $1 $2 $3 $4

	# bind core to COS 
	pqos -a "llc:${HP_COS}=${HP_CPUSET}"
	pqos -a "llc:${LP_COS}=${LP_CPUSET}"	

	pqos -s > $WORK_PATH/pqos_status.txt

	cat $WORK_PATH/pqos_status.txt | grep COS4 >> $WORK_PATH/LLC_allocation.txt
	cat $WORK_PATH/pqos_status.txt | grep COS5 >> $WORK_PATH/LLC_allocation.txt

}

function update_container(){
	# $1 container ID or unique container name
	# $2 CPU sets
	# $3 percentage for CPU quota 1~100 is valiable

	uid=$1
	cpus=$2
	utilization=$3

	docker update --cpuset-cpus=${cpus} --cpu-period=1000000 --cpu-quota=${utilization}0000 ${uid}
}

function update_hp_containers(){
	# $1 CPU sets

	utilization=100
	HP_CPUSET=$1
	for hp in `docker ps -a | grep HP | awk '{print $1}'`
	do
		update_container $hp $HP_CPUSET $utilization
	done

}

function update_lp_containers(){
	# $1 CPU sets

	utilization=100
	LP_CPUSET=$1
	for hp in `docker ps -a | grep LP | awk '{print $1}'`
	do
		update_container $hp $LP_CPUSET $utilization
	done

}
