AEP_COS=6

function llc_mask_aep(){
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

function set_rdt_aep(){
  # Set RDT allocation only
  #
  # $1 aep LLC way
  # $2 aep MBA
  # $3 aep cores
  AEP_CPUSET=$3

  pqos -a "llc:${AEP_COS}=${AEP_CPUSET}"
  pqos -a "llc:${AEP_COS}=${AEP_CPUSET}"

  if [ $MSB_LLC_WAY = 0 ]
  then
    aep_mask=`llc_mask_aep $1 0`
  else
    aep_mask=`llc_mask_aep $1 1`
  fi

  aep_bw=$2

  pqos -e "llc:${AEP_COS}=0x${aep_mask}"
  pqos -e "mba:${AEP_COS}=${aep_bw}"
 
}

function start_specjbb2005_aep(){
    # $1 warehouse setting

    wh=$1
    duration=180000

    result_path="$WORK_PATH/AEP-specjbb_2005_aep"
    mkdir -p $result_path

    echo "!!!==Please double check pmem device is mounted on /mnt==!!!"
    echo "==start test specjbb_2005_aep WH:${wh}=="
    docker run --name AEP-specjbb_2005_aep-${wh}wh --rm --cpuset-cpus=$AEP_CPUSET \
                  -v /mnt:/HEAP -v `pwd`/$result_path:/results -e WAREHOUSE=$wh \
                  -e DURATION=${duration} aep_specjbb2005
	
    stat=$?
    if [ $stat != 0 ]
    then
	    echo "======AEP SPECjbb2015 fail!!!!!"
	    exit 
    fi

}


function start_specjbb2015_aep(){
  # $1 ir setting

  ir=$1
  duration=180000

  opt="-Xmx29g -Xms29g -Xmn27g -XX:+UseG1GC -showversion -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:./gc.log"

  result_path="$WORK_PATH/AEP_specjbb2015_IR${ir}"
  mkdir -p $result_path

  echo "!!!==Please double check pmem device is mounted on /mnt==!!!"
  echo "==start test specjbb2015_aep IR:${ir} (HP)=="
  docker run --name AEP-specjbb2015-IR${ir} --rm -v /mnt:/HEAP -v `pwd`/$result_path:/result -e CONF_IR="${ir}" -e CONF_DURATION=${duration} -e JAVA_OPTS="${opt}" --cpuset-cpus=$AEP_CPUSET aep_specjbb2015
    stat=$?

    if [ $stat != 0 ]
    then
	    echo "=======AEP SPECjbb2005 fail!!!!"
	    exit 
    fi


}
