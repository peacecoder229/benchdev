source hwdrc_osmailbox_config.inc.sh
source resctrl_config.inc.sh  

#2S HT on.
HP_CORES=0-15,64-79,32-47,96-111
LP_CORES=16-31,80-95,48-63,112-127

echo "disable C2,C6"
ret=`cpupower idle-set -d 2`
ret=`cpupower idle-set -d 3`

echo "Set max, min to 2.7Ghz"
ret=`cpupower frequency-set -u 2700Mhz`
ret=`cpupower frequency-set -d 2700Mhz`

pqos -R
init_resctrl

#pare g_CLOSToMEMCLOS for hwdrc_settings_update()
#Map CLOS0-3,8-15 and CLOS4 to MCLOS 0(HP) ,CLOS 5-MCLOS 1, CLOS6- MCLOS 2, CLOS7-MCLOS3(LP)
prepare_CLOStoMCLOS

#MEM_CLOS_ATTRIBUTES 
#config MCLOS 0 with high priority and MCLOS 3 with lowest priority
#MCLOS 0(HP) with MAX delay 0x1, MIN delay 0x1, priority 0x0
#MCLOS 1, with MAX delay 0xFE, MIN delay 0x1, priority 0x5
#MCLOS 2, with MAX delay 0xFE, MIN delay 0x1, priority 0xA
#MCLOS 3(LP), with MAX delay 0xFE, MIN delay 0x1, priority 0xF

g_ATTRIBUTES_MCLOS0=0x00010100
g_ATTRIBUTES_MCLOS1=0x00FE0105
g_ATTRIBUTES_MCLOS2=0x00FE010A
g_ATTRIBUTES_MCLOS3=0x00FE010F

#CONFIG0
#enable MEM_CLOS_EVEMT
#MEM_CLOS_EVENT= 0x80 MCLOS_RPQ_OCCUPANCY_EVENT
#MEM_CLOS_TIME_WINDOW=0x01
#MEMCLOS_SET_POINT=0x01
g_CONFIG0=0x01800101

#Here the OS_MAILBOX is per_socket, so we need to pick a core from the socket you want, one core msr settings will be enough to represent the socket setup
echo "init DRC to default settings for Scoket0"
core_id=1
hwdrc_settings_update
hwdrc_reg_dump

echo "init DRC to default settings for Scoket1"
core_id=33
hwdrc_settings_update
hwdrc_reg_dump

#map CLOS4 to HP_CORES
#map CLOS7 to LP_CORES
associate_cores_to_clos

