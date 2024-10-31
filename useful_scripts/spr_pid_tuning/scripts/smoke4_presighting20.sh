#!/bin/bash
CORES1=32-39,96-103
CORES2=40-47,104-111
CORES3=48-55,112-119
CORES4=56-63,120-127

TIME=5

function benchmark()
{
	core=$1
        tag=$2
	score=$(mlc --loaded_latency -R -t${TIME} -T -k${core} -d0 | grep 00000 | awk '{print $3}')

	echo ============${tag} = ${score}===============
}

function col()
{
	benchmark $CORES2 GROUP2  &
	benchmark $CORES3 GROUP3  &
	benchmark $CORES4 GROUP4  &

	benchmark $CORES1 GROUP1
#       echo "sleep 4" 
#	sleep 4
}


for i in $(seq 1 10000)
do
echo "====test round $i===="

echo "drc"
pqos -R > /dev/null 2>/dev/null
python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null
python2 /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null
#python2 /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null

pqos -a core:4=$CORES1 > /dev/null 2>/dev/null
pqos -a core:5=$CORES2 > /dev/null 2>/dev/null
pqos -a core:6=$CORES3 > /dev/null 2>/dev/null
pqos -a core:7=$CORES4 > /dev/null 2>/dev/null
col

even=$(($i%2))
if [ $even -eq 0 ];then
 echo "sleep 4"
 sleep 4
fi

echo "rdt"
python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null

pqos -R > /dev/null 2>/dev/null
pqos -a core:1=$CORES1 > /dev/null 2>/dev/null
pqos -a core:2=$CORES2 > /dev/null 2>/dev/null
pqos -a core:3=$CORES3 > /dev/null 2>/dev/null
pqos -a core:4=$CORES4 > /dev/null 2>/dev/null

pqos -e mba:1=100 > /dev/null 2>/dev/null
pqos -e mba:2=40 > /dev/null 2>/dev/null
pqos -e mba:3=30 > /dev/null 2>/dev/null
pqos -e mba:4=10 > /dev/null 2>/dev/null

col

done



