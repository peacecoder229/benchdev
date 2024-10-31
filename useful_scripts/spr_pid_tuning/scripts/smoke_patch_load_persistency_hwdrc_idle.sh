

echo "please dump the hwdrc pcode vars-after power on"
read myinput

./hwdrc_icx_2S_xcc_init_to_default_pqos.sh 


echo "please dump the hwdrc pcode vars-after hwdrc enable"
read myinput

for upgrade_microcode in '8df00210' '8df10210' '8df20210' '8df30210' '8df40210' '8df50210' '8df60210' '8df70210' '8df80210' '8df90210'
do
#stress the os patch load. without hwdrc reenable
echo $upgrade_microcode
cat /proc/cpuinfo |grep micro|tail -1

./workload.sh S0 
#if leave backgroud running lp there, the lp will impact the next lp workload!

#we must not disable/re-enable during the test, because that will fix any problems a patch load could have caused
iucode_tool -K/lib/firmware/intel-ucode  /home/longcui/icx_microcode/20210129_8d590210_DRC_21ww04f_config0_write_fix/${upgrade_microcode}_patch_default_server_bios.pdb --overwrite
echo 1 > /sys/devices/system/cpu/microcode/reload
cat /proc/cpuinfo |grep micro|tail -1
./workload.sh S0

echo "please dump the hwdrc pcode vars-after os patch load"
read myinput
done
