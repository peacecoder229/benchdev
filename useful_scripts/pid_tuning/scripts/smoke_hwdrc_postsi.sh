HP_CORES=32-47,96-111
LP_CORES=48-63,112-127

pqos -R

#HP
pqos -a core:4=$HP_CORES
#LP
pqos -a core:7=$LP_CORES

python /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0  
sleep 1
python /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py init 0x0  

echo "====MLC LP only===="
/home/longcui/benchmark/mlc/mlc --loaded_latency -d0 -R -t5 -T -k$LP_CORES |grep 0000

sleep 1

echo "====MLC HP only)===="
/home/longcui/benchmark/mlc/mlc --loaded_latency -d0 -R -t5 -T -k$HP_CORES |grep 0000

sleep 1

echo "====MLC HP+LP mix===="
/home/longcui/benchmark/mlc/mlc --loaded_latency -d0 -R -t5 -T -k$HP_CORES|grep 0000 &
#lp in console
/home/longcui/benchmark/mlc/mlc --loaded_latency -d0 -R -t5 -T -k$LP_CORES|grep 0000

sleep 2

echo "====stream LP only===="
time taskset -c $LP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad 
sleep 1
echo "====stream HP only===="
time taskset -c $HP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad 
sleep 1 
echo "====stream HP+LP mix===="
time taskset -c $HP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad &
time taskset -c $LP_CORES /home/longcui/benchmark/stream/stream_c_200times|grep Triad
