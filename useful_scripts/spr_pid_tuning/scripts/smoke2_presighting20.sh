#!/bin/bash
#HPCORES=32-47,96-111
#LPCORES=48-63,112-127

#D1
HPCORES=24-35,72-83
LPCORES=36-47,84-95

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
	benchmark $LPCORES LP  &

	benchmark $HPCORES HP
}


for i in $(seq 1 10000)
do
echo "====test round $i===="

echo "drc"
pqos -R > /dev/null 2>/dev/null
python2 /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null
python2 /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null
#python2 /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null

pqos -a core:4=$HPCORES > /dev/null 2>/dev/null
pqos -a core:7=$LPCORES > /dev/null 2>/dev/null
col

even=$(($i%2))
if [ $even -eq 0 ];then
 echo "sleep 2"
 sleep 2
fi

echo "rdt"
python2 /home/longcui/benchmark/hwdrc/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null
pqos -R > /dev/null 2>/dev/null
pqos -a core:1=$HPCORES > /dev/null 2>/dev/null
pqos -a core:4=$LPCORES > /dev/null 2>/dev/null

pqos -e mba:1=100 > /dev/null 2>/dev/null
pqos -e mba:4=20 > /dev/null 2>/dev/null

col

done



