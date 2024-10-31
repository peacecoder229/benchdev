source hwdrc_osmailbox_config.inc.sh

pqos -R
umount resctrl


function verify_os_mailbox_read()
{
subaddress=$1
expected_return=$2

#echo $subaddress

hwdrc_read $subaddress

if [ $expected_return != $g_ret_data ]
then
 echo "=====fail:["$subaddress"]return is="$g_ret_data"should be="$expected_return
fi
}

for i in {1..255}
do
#no seed
#RANDOM=$(date +%s)
rand_input_byte1=`expr $RANDOM % 255`
rand_input_byte2=`expr $RANDOM % 255`
rand_input_byte3=`expr $RANDOM % 255`
rand_input_byte4=`expr $RANDOM % 255`

rand_input_byte1_non_zero=`expr $RANDOM % 254 + 1`
rand_input_byte2_non_zero=`expr $RANDOM % 254 + 1`

rand_input_1_10=`expr $RANDOM % 9 + 1`

rand_input_4_digit=`expr $RANDOM % 15`
rand_input_1_digit=`expr $RANDOM % 1`
#echo $rand_input_byte1
#echo $rand_input_byte2
#echo $rand_input_byte3
#echo $rand_input_byte4
#echo $rand_input_4_digit

rand_CLOSToMEMCLOS=`printf "%02x%02x%02x%02x\n" $rand_input_byte1 $rand_input_byte2 $rand_input_byte3 $rand_input_byte4`
#echo $rand_CLOSToMEMCLOS
g_CLOSToMEMCLOS="0x"$rand_CLOSToMEMCLOS

#priority <=F
#max >= min
mclos_max=$rand_input_byte1
if [ $mclos_max == 0 ]
then mclos_min=0
else
mclos_min=`expr $RANDOM % $rand_input_byte1`
fi
#echo $mclos_max,$mclos_min
rand_ATTRIBUTES_MCLOS0=`printf "80%02x%02x%02x\n" $mclos_max $mclos_min $rand_input_4_digit`
g_ATTRIBUTES_MCLOS0="0x"$rand_ATTRIBUTES_MCLOS0

#max >= min
mclos_max=$rand_input_byte2
if [ $mclos_max == 0 ]
then mclos_min=0
else
mclos_min=`expr $RANDOM % $rand_input_byte2`
fi
#echo $mclos_max,$mclos_min
rand_ATTRIBUTES_MCLOS1=`printf "81%02x%02x%02x\n" $mclos_max $mclos_min $rand_input_4_digit`
g_ATTRIBUTES_MCLOS1="0x"$rand_ATTRIBUTES_MCLOS1

#max >= min
mclos_max=$rand_input_byte3
if [ $mclos_max == 0 ]
then mclos_min=0
else
mclos_min=`expr $RANDOM % $rand_input_byte3`
fi
#echo $mclos_max,$mclos_min
rand_ATTRIBUTES_MCLOS2=`printf "82%02x%02x%02x\n" $mclos_max $mclos_min $rand_input_4_digit`
g_ATTRIBUTES_MCLOS2="0x"$rand_ATTRIBUTES_MCLOS2

#max >= min
mclos_max=$rand_input_byte4
if [ $mclos_max == 0 ]
then mclos_min=0
else
mclos_min=`expr $RANDOM % $rand_input_byte4`
fi
#echo $mclos_max,$mclos_min
rand_ATTRIBUTES_MCLOS3=`printf "83%02x%02x%02x\n" $mclos_max $mclos_min $rand_input_4_digit`
g_ATTRIBUTES_MCLOS3="0x"$rand_ATTRIBUTES_MCLOS3

##ERRPR:0.can not set the event_en to 0
##1.timer_interval is non zero 2.event_enable non zero. in expectation
rand_CONFIG0=`printf "01%02x%02x%02x\n" $rand_input_byte1_non_zero $rand_input_1_10 $rand_input_byte2`
#rand_CONFIG0=0800101
#echo $rand_CONFIG0
g_CONFIG0="0x"$rand_CONFIG0

core_id=1
hwdrc_settings_update > /dev/null
#hwdrc_settings_update 


verify_os_mailbox_read 0x800001d1 $rand_CLOSToMEMCLOS

verify_os_mailbox_read 0x800002d1 $rand_ATTRIBUTES_MCLOS0
verify_os_mailbox_read 0x800102d1 $rand_ATTRIBUTES_MCLOS1
verify_os_mailbox_read 0x800202d1 $rand_ATTRIBUTES_MCLOS2
verify_os_mailbox_read 0x800302d1 $rand_ATTRIBUTES_MCLOS3

verify_os_mailbox_read 0x800003d1 $rand_CONFIG0

verify_os_mailbox_read 0x800004d1 00000003

printf "."

done
