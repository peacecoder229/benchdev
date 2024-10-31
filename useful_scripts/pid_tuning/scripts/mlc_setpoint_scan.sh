
let i=0;while true;do let i+=1;
echo =====test round $i=====;
sleep 1;
./hwdrc_change_setpoint.sh $i
./workload.sh S0 

done 

