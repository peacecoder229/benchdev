

#HP_CORES=$1
#LP_CORES=48-63,112-127

#XCC D0 QWAE:32C 300W, 2.9Ghz,2S HT on.
#NUMA node0 CPU(s):   0-31,64-95
#NUMA node1 CPU(s):   32-63,96-127
#HP_CORES=0-15,64-79,32-47,96-111
#LP_CORES=16-31,80-95,48-63,112-127

#XCC D1 QWMA, Ali customized SKU:24C, 185W, 2.5Ghz,2S HT on
#NUMA node0 CPU(s):     0-23,48-71
#NUMA node1 CPU(s):     24-47,72-95
#HP_CORES=0-11,48-59,24-35,72-83
#LP_CORES=12-23,60-71,36-47,84-95


function invalind_params()
{
echo "./workload.sh on [S0|S1] [core_list_for_HP]"
echo "S0/S1:workload on Socket0 or Socket1"
echo "core_list_for_HP:core list for High priority TASK.Low priority work load on 32 cores"
echo "Samples:"
echo "1)run 2 MLC workloads on S0 with 2 MEM CLOS:"
echo "./workload.sh S0"
echo "2)run 2 MLC workload on S1, specify the core 32-47 to HP workload"
echo "./workload.sh S1 32-47"

exit 1
}

if [ $# -eq 0 ]; then

invalind_params

elif [ $# -eq 1 ]; then
  if [ $1 == "S0" ];then
  echo "workload on Socket 0"
  #D0
  HP_CORES=0-23
  LP_CORES=24-47

  #D1
  #HP_CORES=0-11,48-59
  #LP_CORES=12-23,60-71

  elif [ $1 == "S1" ];then 
  echo "workload on Socket 1"
  #D0
  #HP_CORES=32-47,96-111
  #LP_CORES=48-63,112-127
  #D1
  HP_CORES=24-35,72-83
  LP_CORES=36-47,84-95

  else
  invalind_params
  fi
elif [ $# -eq 2 ]; then
  if [ $1 == "S0" ];then
  echo "workload on Socket 0"
  HP_CORES=$2
  #D0
  #LP_CORES=16-31,80-95
  #D1
  LP_CORES=12-23,60-71
  elif [ $1 == "S1" ];then
  echo "workload on Socket 1"
  HP_CORES=$2
  #D0
  #LP_CORES=48-63,112-127
  #D1
  LP_CORES=36-47,84-95
  else
  invalind_params
  fi
else
invalind_params
fi


#TIME=5
TIME=30

function benchmark()
{
        core=$1
        tag=$2
        score=$(mlc --loaded_latency -R -t${TIME} -T -k${core} -d0 | grep 00000 | awk '{print $3}')

        printf "=%s=%.1f=" $tag $score
}

function col()
{

        benchmark $LP_CORES lp &
        lp_process_id=$!
        benchmark $HP_CORES hp
        ##sleep 2
        #wait for lp process finished
        #other wise, it may impact the next mlc workload calc
        wait $!
}

function col_ngx()
{

        benchmark $LP_CORES lp &
        lp_process_id=$!
	cd /root/run_nginx
	./runngxwrk2.sh 1-16 500000 2000 48-63 10002 64
        ##sleep 2
        #wait for lp process finished
        #other wise, it may impact the next mlc workload calc
        wait $!
}

echo "HP_CORES="$HP_CORES
echo "LP_CORES="$LP_CORES
#<<'COMMENT'

printf "====MLC LP NGINX  HP HP+LP mix====\n"
#benchmark $LP_CORES lp

##sleep 1
##echo "sleep 1" 
#printf "====MLC HP only===="
#benchmark $HP_CORES hp

##sleep 1
##echo "sleep 1" 
#COMMENT

printf "====MLC HP+LP mix===="
col_ngx

printf "\n"

<<'COMMENT'
#echo "====stream HP+LP mix===="
#time taskset -c $HP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad &
#time taskset -c $LP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad

echo "====stream LP only===="
taskset -c $LP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad 

sleep 1
echo "sleep 1" 

echo "====stream HP only===="
taskset -c $HP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad 

sleep 1
echo "sleep 1" 

echo "====stream HP+LP mix===="
taskset -c $LP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad &
taskset -c $HP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad
COMMENT
