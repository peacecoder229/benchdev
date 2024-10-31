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

function col_in_backgroud()
{
	time benchmark $LPCORES LP  &

	time benchmark $HPCORES HP  &
}

function col()
{
	time benchmark $LPCORES LP  &

	time benchmark $HPCORES HP  
}

##pqos -R > /dev/null 2>/dev/null
##python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null
##python2 /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null
#python2 /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0 > /dev/null 2>/dev/null

./hwdrc_icx_2S_xcc_init_to_default_pqos.sh 

pqos -a core:4=$HPCORES 
pqos -a core:7=$LPCORES #> /dev/null 2>/dev/null

echo "start drc 5 seconds test with HP and LP workload "
col_in_backgroud

sleep 5 

echo "disable the DRC while the workload is there :MCLOS_EN=0"

#python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 > /dev/null 2>/dev/null
./hwdrc_icx_2S_xcc_disable.sh 

sleep 10 
echo "wait for backgroud workload finish"


echo "start new colocation test without DRC"
col


echo "start colocation test with MBA reset"

pqos -R > /dev/null 2>/dev/null
pqos -a core:1=$HPCORES > /dev/null 2>/dev/null
pqos -a core:4=$LPCORES > /dev/null 2>/dev/null

pqos -e mba:1=100 > /dev/null 2>/dev/null
pqos -e mba:4=20 > /dev/null 2>/dev/null

col

