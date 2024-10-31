init_resctrl(){

echo "remount resctrl to reset the CLOS setting"
umount resctrl
mount resctrl -t resctrl /sys/fs/resctrl/ 
mkdir -p /sys/fs/resctrl/{C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14}

}

g_mapclostomclos=0
g_CLOSToMEMCLOS=0

map_clos_to_mclos(){
#map CLOS to MCLOS
#input 1:CLOS (C01~C14)
#input 2:MCLOS (0~3)
#return in $g_mapclostomclos
clos=$1
mclos=$2

closid=`cat /sys/fs/resctrl/$clos/closid`
g_mapclostomclos=$[mclos << closid *2]

}

prepare_CLOStoMCLOS(){
#map CLOS4 to MCLOS0 HP
#map CLOS5 to MCLOS1 
#map CLOS6 to MCLOS2
#map CLOS7 to MCLOS3 LP
#return in $g_CLOSToMEMCLOS

map_clos_to_mclos C04 0
g_CLOSToMEMCLOS=$[g_CLOSToMEMCLOS + g_mapclostomclos]

map_clos_to_mclos C05 1
g_CLOSToMEMCLOS=$[g_CLOSToMEMCLOS + g_mapclostomclos]

map_clos_to_mclos C06 2
g_CLOSToMEMCLOS=$[g_CLOSToMEMCLOS + g_mapclostomclos]

map_clos_to_mclos C07 3
g_CLOSToMEMCLOS=$[g_CLOSToMEMCLOS + g_mapclostomclos]

#printf 'CLOSToMEMCLOS=%x\n' $g_CLOSToMEMCLOS
}

associate_cores_to_clos(){

echo "map CLOS4 to HP_CORES:"$HP_CORES
echo "map CLOS7 to LP_CORES:"$LP_CORES

echo $HP_CORES>/sys/fs/resctrl/C04/cpus_list
echo $LP_CORES>/sys/fs/resctrl/C07/cpus_list

#cat /sys/fs/resctrl/{C04,C05,C06,C07}/cpus_list
}

