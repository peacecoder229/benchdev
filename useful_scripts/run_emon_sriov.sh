#!/bin/sh
DELAY=$1
EMONNAME=$2
CASE=$3
EMON_ROOT=/mnt/nvme/pnpdata_original/emon
OUTPUT_DIR=/mnt/nvme/pnpdata_original/emon/results
export PATH=$EMON_ROOT:$PATH
SUF=
EMON_EVENT=$EMON_ROOT/clx-1s-events.txt
EMON_XML=$EMON_ROOT/clx-1s.xml
/opt/intel/sep/sepdk/src/rmmod-sep${SUF}
/opt/intel/sep/sepdk/src/insmod-sep${SUF}
sleep 3;
source /opt/intel/sep/sep_vars.sh
#source /root/emon/sep_3.16_linux_414852/sep_vars.sh
#DATE=`date +%Y-%m-%d-%H:%M:%S`
#emon -v > /root/emon/results/${DATE}${1}-v_0.dat
#emon -M > /root/emon/results/${DATE}${1}-m_0.dat
mkdir -p $OUTPUT_DIR/${CASE}


emon -v > $OUTPUT_DIR/$CASE/${EMONNAME}-v_0.dat
emon -M > $OUTPUT_DIR/$CASE/${EMONNAME}-m_0.dat

emon -i $EMON_EVENT -s${DELAY}  > $OUTPUT_DIR/$CASE/${EMONNAME}_0.out &

#sleep 100

#emon -stop

#emon -i /root/emon/bdx-ep-events-for-ripan.txt > /root/emon/results/${DATE}${1}_0.out

