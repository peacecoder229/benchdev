# This code only purpose is to understand arrays in shell. it does not have any use
#arr=(0 0 0 0 0 )
MOVING_AVERAGE_WINDOW=50
moving_average=0;
moving_sum=0;
moving_index=0
for (( i = 0 ; i < MOVING_AVERAGE_WINDOW; i++))
do
	moving_arr[$i]=0
	#echo "value is ${moving_arr[$i]}"
done

for ((i = 0; i< 500 ; i++ ))
do
	value=$((i%37))
	#index=$(($i%MOVING_AVERAGE_WINDOW))
	moving_sum=$((moving_sum+value))	
	moving_sum=$(( moving_sum - ${moving_arr[$moving_index]} )) ;
	moving_arr[$moving_index]=$value;
	#echo "$moving_index= $(( (moving_index +1)%MOVING_AVERAGE_WINDOW )) "
	moving_index2=$((moving_index+1))
	moving_index=$((moving_index2%MOVING_AVERAGE_WINDOW))
	moving_average=$(echo "$moving_sum/$MOVING_AVERAGE_WINDOW" | bc )
	echo "moving sum is $moving_sum, the moving index is $moving_index, moving average is: $moving_average "
	#echo "this is a test $i "
	#echo " ${arr[$i]}"	
done

#index=0
#for ((i = 0; i< 500 ; i++ ))
#do
#	index2=$(($i%50))
#       echo "${arr[$index2]}"
#
#done

