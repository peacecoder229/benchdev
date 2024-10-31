source hwdrc_osmailbox_config.inc.sh

#XCC D0 QWAE:32C 300W, 2.9Ghz,2S HT on.
#NUMA node0 CPU(s):   0-31,64-95
#NUMA node1 CPU(s):   32-63,96-127
#HP_CORES=0-15,64-79,32-47,96-111
#LP_CORES=16-31,80-95,48-63,112-127

#XCC D1 QWMA, Ali customized SKU:24C, 185W, 2.5Ghz,2S HT on
#NUMA node0 CPU(s):     0-23,48-71
#NUMA node1 CPU(s):     24-47,72-95
HP_CORES=0-11,48-59,24-35,72-83
LP_CORES=12-23,60-71,36-47,84-95

echo "disable C2,C6"
ret=`cpupower idle-set -d 2`
ret=`cpupower idle-set -d 3`

echo "Set max, min to 2.7Ghz"
ret=`cpupower frequency-set -u 2700Mhz`
ret=`cpupower frequency-set -d 2700Mhz`

pqos -R
umount /sys/fs/resctrl

echo "disable DRC for Scoket0"
core_id=1
hwdrc_disable

echo "disable DRC for Scoket1"
#D0
#core_id=33
#D1
core_id=25
hwdrc_disable
