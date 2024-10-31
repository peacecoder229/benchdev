DELAY=${1:-2}
EMONNAME=$2
CASE=$3
EMON_ROOT=/root/Nizar/emon
OUTPUT_DIR=/root/Nizar/emon/results
export PATH=$EMON_ROOT:$PATH
SUF=
EMON_EVENT=/root/Nizar/emon/clx-1s-events.txt
EMON_XML=/root/Nizar/emon/clx-1s.xml
/opt/intel/sep/sepdk/src/rmmod-sep${SUF}
/opt/intel/sep/sepdk/src/insmod-sep${SUF}
sleep 3
source /opt/intel/sep/sep_vars.sh

mkdir -p $OUTPUT_DIR/${CASE}
echo "emon -v > $OUTPUT_DIR/$CASE/${EMONNAME}-v_0.dat"
emon -v > $OUTPUT_DIR/$CASE/${EMONNAME}-v_0.dat
echo "emon -M > $OUTPUT_DIR/$CASE/${EMONNAME}-m_0.dat"
emon -M > $OUTPUT_DIR/$CASE/${EMONNAME}-m_0.dat

echo "emon -i $EMON_EVENT -s${DELAY}  > $OUTPUT_DIR/$CASE/${EMONNAME}_0.out &"
emon -i $EMON_EVENT -s${DELAY}  > $OUTPUT_DIR/$CASE/${EMONNAME}_0.out &

control_c() {
    emon -stop
    echo "finihsed data collection"
    exit
}

trap control_c SIGINT

for(( i=0 ; i< 100 ; i++ )) 
do
    sleep 1
done
emon -stop

