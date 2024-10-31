

echo "please dump the hwdrc pcode vars-after power on"
read myinput

./hwdrc_icx_2S_xcc_init_to_default_pqos.sh 


echo "please dump the hwdrc pcode vars-after hwdrc enable"
read myinput

for upgrade_microcode in '8df001b0' '8df101b0' '8df201b0' '8df301b0' '8df401b0' '8df501b0' '8df601b0' '8df701b0' '8df801b0' '8df901b0'
#for upgrade_microcode in  '8df901b0'
do
#stress the os patch load. without hwdrc reenable
echo $upgrade_microcode
cat /proc/cpuinfo |grep micro|tail -1

./workload.sh S0 
#if leave backgroud running lp there, the lp will impact the next lp workload!


iucode_tool -K/lib/firmware/intel-ucode  /home/longcui/icx_microcode/20210119_8d6701b0_DRC_20ww48a_addmore_dbg_patchload/${upgrade_microcode}_patch_default_server_bios.pdb --overwrite

echo "please prepare dump the hwdrc pcode vars-after os patch load,#echo 2 > /sys/devices/system/cpu/microcode/reload"
read myinput

./workload.sh S0 
#sleep 1
#we must not disable/re-enable during the test, because that will fix any problems a patch load could have caused
#echo 2 > /sys/devices/system/cpu/microcode/reload
cat /proc/cpuinfo |grep micro|tail -1
done
