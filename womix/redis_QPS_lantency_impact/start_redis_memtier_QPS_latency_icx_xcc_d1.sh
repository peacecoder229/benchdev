#!/bin/bash
ulimit -n 65535
#REDIS_CMD=redis-server
REDIS_CMD=/home/longcui/benchmark/redis/redis-4.0.10/src/redis-server
MEMTIER_CMD=/home/longcui/benchmark/redis/memtier_benchmark/memtier_benchmark_2ms

#ICX D1 24C,2S
#NUMA node0 CPU(s):     0-23,48-71
#NUMA node1 CPU(s):     24-47,72-95

#socket0
#REDIS_CORES={{12..23},{60..71}
#BWAVES_CORES=`{{0..11},{48..59}}`
#Socket1
#MEMTIER_CORES={{36-47,84-95}}

last_redis=0
last_memtier=0

start_redis-server(){

    echo "start redis server"
    for i in {{12..23},{60..71}}
    do
      echo "running redis on core$i port@$port"
      taskset -c $i $REDIS_CMD --port ${port} > /dev/null 2>&1&
      last_redis=$!
      port=$((${port}+1))
    done

    sleep 3

    mpstat -P `echo {{12..23},{60..71}} |sed -e 's/ /,/g'` 30 1 > logs/cpuutil/test${1}-cpu.log&

}

start_memtier_benchmark(){

    echo "start memtier client"
    for i in {{36..47},{84..95}} 
    do
      echo "running memtier on core$i,port@$port" 
      taskset -c $i $MEMTIER_CMD -s localhost -p ${port} --pipeline=30 -c 1 -t 1 -d 1024 --key-maximum=42949 --key-pattern=G:G --key-stddev=1177 --ratio=1:1 --distinct-client-seed --random-data --test-time=60 --run-count=1 --hide-histogram &>logs/${1}/redis-core${i}.log &
      last_memtier=$!
      echo $last_memtier
      port=$((${port}+1))
    done
   
    if [ $1 == 1 ]
    then
    sleep 1
    else
    #only for response time
    sleep 10
    start_bwaves 
    fi

    wait $last_memtier
    killall redis-server 
}

start_bwaves(){
    instanceNum=24
    echo "start lp"
    #docker run --cpuset-cpus=0-11,48-59 --name speccpuBwaves --rm -e INSTANCES=$instanceNum -e WORKLOAD=bwaves spec17:0.6 > /dev/null 2>&1&
    docker run --privileged --cpuset-cpus=0-11,48-59 --name speccpuBwaves --rm -e INSTANCES=${instanceNum} --cpuset-mems=0  -v `pwd`/test:/home/spec17/result/ -e WORKLOAD=bwaves_s speccpu2017:latest > /dev/null 2>&1&
    #sleep 20
}


function colocation(){
    echo "********************************************************************"
    echo "****************************start test $1****************************"
    echo "********************************************************************"

    #sleep 10
    #start_bwaves 

    port=7777
    start_redis-server $1

    port=7777
    start_memtier_benchmark $1


    ps aux |grep -E 'redis-server\ \*:|$MEMTIER_CMD \-s|starter.py\ imc_config.json'|awk '{print $2}' | while read line;
 do kill -9 $line; done
    docker stop speccpuBwaves
}

function set_mba_10(){
    echo "set LP MBA=10"
#map CLOS1 to povray
#map CLOS2 to perlbench
    pqos -e "llc:1=0x7ff"
    pqos -e "llc:2=0x7ff"
    pqos -e "mba:1=100"
    pqos -e "mba:2=10"
#Apply to
#HP

#REDIS_CORES={{12..23},{60..71}
#BWAVES_CORES=`{{0..11},{48..59}}`
 
    pqos -a "llc:1=12-23,60-71"
    pqos -a "llc:2=0-11,48-59"
    sleep 3
}

main() {

  rm logs -rf
#Disable C6,C2:
cpupower idle-set -d 2
cpupower idle-set -d 3

#Set max, min to 2.7Ghz:
cpupower frequency-set -u 2700Mhz
cpupower frequency-set -d 2700Mhz

  pqos -R
  CORES=$1
  CORESIndex=$[$CORES-1]

  mkdir logs
  cd logs
  for i in {1..4}
  do
    mkdir $i
  done
  mkdir cpuutil
  cd ..

  #redis+memtier only
  colocation 1

  #redis+memtier(HP)  + bwaves- no rdt
  colocation 2

  #redis+memtier(HP)  + bwaves- MBA=10
  pqos -R
  set_mba_10
  colocation 3

  #redis+memtier(HP)  + bwaves- DRC ,setpoint=2
  pqos -R
  source ./hwdrc_init_to_default_pqos_icx_2S_xcc_d1.sh
  source ./hwdrc_reg_dump_msr.sh
  pqos -m all:[12-23,60-71][36-47,84-95][0-11,48-59] -i 1 -o logs/pqos_mon_test.log & 
  colocation 4
  
  #disable MEMCLOS DRC
  #RD_WR=WR
  #MEMCLOS_EN=0
  wrmsr -p 1 0xb1 0x80000000
  wrmsr -p 1 0xb0 0x810004d2
  echo "MEMCLOS_EN=0"
  rdmsr -p 1 0xb1;rdmsr -p 1 0xb0
  sleep 1;

  sync
  killall pqos
  sync
  sed -e 's//\n/g' ./logs/4/redis-core36.log |awk '{print $10,$17}' > ./logs/hwdrc_raw_36.log
  grep -r "0-11,48-" ./logs/pqos_mon_test.log|awk '{print $5,$6}' > ./logs/mbm_0-11_bwaves_LP.txt
  grep -r "12-23,60" ./logs/pqos_mon_test.log|awk '{print $5,$6}' > ./logs/mbm_12-23_redis_HP.txt
  grep -r "36-47,84" ./logs/pqos_mon_test.log|awk '{print $5,$6}' > ./logs/mbm_36-47_memtier_HP.txt
 
  pqos -R
  pqos -r -t 1
}

main "$@"
