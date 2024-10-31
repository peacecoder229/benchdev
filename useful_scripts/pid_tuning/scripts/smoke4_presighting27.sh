#!/bin/bash


#XCC D0 QWAE:32C 300W, 2.9Ghz,2S HT on.
#NUMA node0 CPU(s):   0-31,64-95
#NUMA node1 CPU(s):   32-63,96-127
CORES1=32-39,96-103
CORES2=40-47,104-111
CORES3=48-55,112-119
CORES4=56-63,120-127

#XCC D1 QWMA, Ali customized SKU:24C, 185W, 2.5Ghz,2S HT on
#NUMA node0 CPU(s):     0-23,48-71
#NUMA node1 CPU(s):     24-47,72-95
CORES1=24-29,72-77
CORES2=30-35,78-83
CORES3=36-41,84-89
CORES4=42-47,90-95

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
	sleep 4
}


echo base
#python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0
./hwdrc_icx_2S_xcc_disable.sh
pqos -R > /dev/null 2>/dev/null
col

echo rdt
#python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0
./hwdrc_icx_2S_xcc_disable.sh

pqos -R > /dev/null 2>/dev/null
pqos -a core:1=$CORES1 > /dev/null 2>/dev/null
pqos -a core:2=$CORES2 > /dev/null 2>/dev/null
pqos -a core:3=$CORES3 > /dev/null 2>/dev/null
pqos -a core:4=$CORES4 > /dev/null 2>/dev/null

pqos -e mba:1=100 > /dev/null 2>/dev/null
pqos -e mba:2=70 > /dev/null 2>/dev/null
pqos -e mba:3=40 > /dev/null 2>/dev/null
pqos -e mba:4=10 > /dev/null 2>/dev/null

col

echo "drc"
pqos -R
#python2 /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0
./hwdrc_icx_2S_xcc_init_to_default_pqos.sh 

pqos -a core:4=$CORES1
pqos -a core:5=$CORES2
pqos -a core:6=$CORES3
pqos -a core:7=$CORES4
col
