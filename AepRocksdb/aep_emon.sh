EMON_DIR="/opt/intel/sep"
EMON_CIF="/root/skx-2s-events.txt"
RESULT="/root"

rm -f $RESULT/emon-v.dat
rm -f $RESULT/emon-m.dat
rm -f $RESULT/emon-d.dat

source $EMON_DIR/sep_vars.sh
$EMON_DIR/sepdk/src/insmod-sep -g root

emon -v >>$RESULT/emon-v.dat
emon -M >>$RESULT/emon-m.dat
sleep 900

emon -i $EMON_CIF -f $RESULT/emon-d.dat &
while true
do
   if [ `ps -aux| grep "fio 1M" | wc -l` -lt 2 ]; then
      echo -e "fio stop, stop emon...."
      emon -stop
      break
   else
      continue
   fi
   sleep 2
done


