#!/bin/bash

source hwdrc_osmailbox_config.inc.sh

#XCC D0 QWAE:32C 300W, 2.9Ghz,2S HT on.
#NUMA node0 CPU(s):   0-31,64-95
#NUMA node1 CPU(s):   32-63,96-127
#HP_CORES=0-15,64-79,32-47,96-111
#LP_CORES=16-31,80-95,48-63,112-127

#XCC D1 QWMA, Ali customized SKU:24C, 185W, 2.5Ghz,2S HT on
#NUMA node0 CPU(s):     0-23,48-71
#NUMA node1 CPU(s):     24-47,72-95

#HP_CORES=0-11,48-59,24-35,72-83
HP_CORES=0-17
#LP_CORES=12-23,60-71,36-47,84-95
LP_CORES=18-35

#numa remote access test

#LP_CORES=0-23,48-71,24-47,72-95


echo "disable C2,C6"
ret=`cpupower idle-set -d 2`
ret=`cpupower idle-set -d 3`

echo "Set max, min to 2.7Ghz"
ret=`cpupower frequency-set -u 2700Mhz`
ret=`cpupower frequency-set -d 2700Mhz`

pqos -R
umount resctrl

#pare g_CLOSToMEMCLOS for hwdrc_settings_update()
#Assume MCLOS0 is highest priority and MCLOS1-2 has lower priority accordingly, MCLOS 3 with lowest priority
#Map CLOS 0-3, 8-15 and CLOS4 to MCLOS 0(HP), CLOS 5-MCLOS 1, CLOS6- MCLOS 2, CLOS7-MCLOS3(LP)
g_CLOSToMEMCLOS=0x0000E400

#MEM_CLOS_ATTRIBUTES 
#config MCLOS 0 with high priority and MCLOS 3 with lowest priority
#set MEM_CLOS_ATTR_EN for all 4 mclos.
#MCLOS 0(HP) with MAX delay 0x1, MIN delay 0x1, priority 0x0
#MCLOS 1, with MAX delay 0xFE, MIN delay 0x1, priority 0x5
#MCLOS 2, with MAX delay 0xFE, MIN delay 0x1, priority 0xA
#MCLOS 3(LP), with MAX delay 0xFE, MIN delay 0x1, priority 0xF

g_ATTRIBUTES_MCLOS0=0x80010100
g_ATTRIBUTES_MCLOS1=0x81FF0105
g_ATTRIBUTES_MCLOS2=0x82FF010a
g_ATTRIBUTES_MCLOS3=0x83FF010F

#CONFIG0
#enable MEM_CLOS_EVEMT
#MEM_CLOS_EVENT= 0x80 MCLOS_RPQ_OCCUPANCY_EVENT
#MEM_CLOS_TIME_WINDOW=0x01
#MEMCLOS_SET_POINT=0x01
input_setponit=$1
g_CONFIG0=`printf "0x%08x\n" $((0x01800100 + input_setponit))`

#Here the OS_MAILBOX is per_socket, so we need to pick a core from the socket you want, one core msr settings will be enough to represent the socket setup
echo "init DRC to default settings for Scoket0"
core_id=1
hwdrc_settings_update
hwdrc_reg_dump

echo "init DRC to default settings for Scoket1"
#D0
#core_id=33
#D1
core_id=25
hwdrc_settings_update
hwdrc_reg_dump

#map CLOS4 to HP_CORES
#map CLOS7 to LP_CORES
pqos -e llc:7=0xfff
pqos -e llc:4=0xfff

pqos -a llc:7=$LP_CORES
pqos -a llc:4=$HP_CORES

