#!/bin/bash

#  INTEL CONFIDENTIAL

# Copyright 2016 Intel Corporation All Rights Reserved.
# The source code contained or described herein and all documents related
# to the source code ("Material") are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel
# Corporation or its suppliers and licensors. The Material may contain
# trade secrets and proprietary and confidential information of Intel
# Corporation and its suppliers and licensors, and is protected by worldwide
# copyright and trade secret laws and treaty provisions. No part of the
# Material may be used, copied, reproduced, modified, published, uploaded,
# posted, transmitted, distributed, or disclosed in any way without
# Intel's prior express written permission.

# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property rights
# must be express and approved by Intel in writing.

# Unless otherwise agreed by Intel in writing, you may not remove or alter
# this notice or any other notice embedded in Materials by Intel or
# Intel's suppliers or licensors in any way.

usage ()
{
  echo 'Usage : hwpdesire.sh  -c|--core core -f|--freq <frequency_in_KHz>	set specific frequency'  
  echo '	hwpdesire.sh  -c|--core core -m|--min <frequency_in_KHz>	set min frequency'  
  echo '	hwpdesire.sh  -c|--core core -a|--max <frequency_in_KHz>	set max frequency'  
  echo '        hwpdesire.sh  -r|--reset	reset all core frequency to default setting'
  echo '        hwpdesire.sh  -h|--help		print this help'
  
}
function_check() {
#check cpuid to be implemented

kernel_version=`uname -r`
echo "kernel Version: ". $kernel_version
Mnum=$(uname -r| awk -F. '{print $1}')
Snum=$(uname -r| awk -F. '{print $2}')
if [ $Mnum -gt 4 ] || ([ $Mnum -eq 4 ]&& [ $Snum -ge 11 ]) ; then
	echo "Check Kernel version: OK!"
else
	echo "Check Kernel Version: too low, can't be configured! Configure is aborted..."
	exit 1
fi

if [ `whoami` = "root" ];then
	echo "Check Permission: root user, OK!"
else
	echo "Check Permission: not root user, permission denied."
	exit 1
fi
}

function_reset() {
	# reset to system default value
	 hdMinFreq=`cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq`
         hdMaxFreq=`cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq`
         hdMinFreq=`echo "obase=16;$(($hdMinFreq/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`
         hdMaxFreq=`echo "obase=16;$(($hdMaxFreq/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`


	echo "Rest all cores to max:"$hdMaxFreq"min:"$hdMinFreq
	wrmsr -a 0x774 '0x8000'$hdMaxFreq$hdMinFreq
}

disable_C1E_C3_C6() {
	# disable C1E, C3, C6
	cpupower idle-set -e 0
	cpupower idle-set -e 1
	cpupower idle-set -d 2
	cpupower idle-set -d 3
#	cpupower idle-set -d 4
}

ARGS=`getopt -o hc:m:a:f:r --long help,core:,freq:reset:min:max: \
             -n 'example.sh' -- "$@"`

if [ $? != 0 ] ; then usage; exit 1 ; fi

# Note the quotes around `$TEMP': they are essential!
eval set -- "$ARGS"

while true; do
    case "$1" in
	 -h|--help)
		usage
		shift
			;;
	-c|--core)
	if [ x$2 != x ]; then
		core=$2
		parsed_core=""
		for num in $(tr ',' ' '  <<< "$core"); do
			if [[ "$num" == *-* ]]; then
				num=${num/-/..}
				num=`eval echo {$num}`
				result=`echo ${num// /,}`
			else
				result="$num"
			fi
			parsed_core="$parsed_core,$result"
		done
		parsed_core=${parsed_core:1}
		echo "changed cores:$parsed_core"
	else
		echo "please input the user specific core!"
		exit 1
	fi
	shift 2
	;;
	-a|--max)
		# set power policy
		if [ x$2 != x ]; then
			maxFreq=`echo "obase=16;$(($2/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`

			if [ ! $core ]; then
				allCores=$(cat /proc/cpuinfo | grep process | awk '{print $3}')
				for core in $allCores
	    				do
       			 		status=`rdmsr -p ${core} 0x770 -f 0:0`
				        if [[ ${status} == 1 ]]; then
				            echo "Core[${core}]:HWP is enabled"
					    echo "Set max:  $2 in $maxFreq"
					    orimsr=`rdmsr -p ${core} 0x774`
					    desmsr=`printf "%#x\n" $(( 0x$orimsr & 0xffff00ff ))`
					    desmsr=`printf "%#x\n" $(( $desmsr | 0x0000${maxFreq}00 ))`
					    echo $desmsr
					    wrmsr -p $core 0x774 $desmsr
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core max frequency is set to "$2"KHZ, msr: $final

				        else
				            echo "Core[${core}]:HWP is Disabled"
				        fi
				done	
			else
				IFS=',' read -r -a cores <<< "$parsed_core"
				for core in ${cores[@]}
					do
					status=`rdmsr -p $core 0x770 -f 0:0`
                                        if [[ ${status} == 1 ]]; then
                                            echo "Core[${core}]:HWP is enabled"
				            echo "Set max: $2 = $maxFreq "
					    orimsr=`rdmsr -p ${core} 0x774`
					    desmsr=`printf "%#x\n" $(( 0x$orimsr & 0xffff00ff ))`
					    desmsr=`printf "%#x\n" $(( $desmsr | 0x0000${maxFreq}00 ))`
					    echo $desmsr
					    wrmsr -p $core 0x774 $desmsr
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core max frequency is set to "$2"KHZ, msr: $final!
		
                                        else
                                            echo "Core[${core}]:HWP is Disabled"
                                        fi
 
				done
			fi
		else
			echo "please input the user specific frequency in KHZ!"
			exit 1
		fi
		shift 2
            ;;

	-m|--min)
		# set power policy
		if [ x$2 != x ]; then
			minFreq=`echo "obase=16;$(($2/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`

			if [ ! $core ]; then
				allCores=$(cat /proc/cpuinfo | grep process | awk '{print $3}')
				for core in $allCores
	    				do
       			 		status=`rdmsr -p ${core} 0x770 -f 0:0`
				        if [[ ${status} == 1 ]]; then
				            echo "Core[${core}]:HWP is enabled"
					    echo "Set min:  $2 in $minFreq"
					    orimsr=`rdmsr -p ${core} 0x774`
					    desmsr=`printf "%#x\n" $(( 0x$orimsr & 0xffffff00 ))`
					    desmsr=`printf "%#x\n" $(( $desmsr | 0x000000$minFreq ))`
					    echo $desmsr
					    wrmsr -p $core 0x774 $desmsr
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core min frequency is set to "$2"KHZ, msr: $final!

				        else
				            echo "Core[${core}]:HWP is Disabled"
				        fi
				done	
			else
				IFS=',' read -r -a cores <<< "$parsed_core"
				for core in ${cores[@]}
					do
					status=`rdmsr -p $core 0x770 -f 0:0`
                                        if [[ ${status} == 1 ]]; then
                                            echo "Core[${core}]:HWP is enabled"
				            echo "Set min: $2 = $minFreq "
					    orimsr=`rdmsr -p ${core} 0x774`
					    desmsr=`printf "%#x\n" $(( 0x$orimsr & 0xffffff00 ))`
					    desmsr=`printf "%#x\n" $(( $desmsr | 0x000000$minFreq ))`
					    echo $desmsr
					    wrmsr -p $core 0x774 $desmsr
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core min frequency is set to "$2"KHZ, msr: $final!
					  
		
                                        else
                                            echo "Core[${core}]:HWP is Disabled"
                                        fi
 
				done
			fi
		else
			echo "please input the user specific frequency in KHZ!"
			exit 1
		fi
		shift 2
            ;;
	-f|--freq)
		# precheck
	#	function_check
		hdMinFreq=`cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq`
		hdMaxFreq=`cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq`
		hdMinFreq=`echo "obase=16;$(($hdMinFreq/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`
		hdMaxFreq=`echo "obase=16;$(($hdMaxFreq/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`

		# set power policy
		if [ x$2 != x ]; then
			desireFreq=`echo "obase=16;$(($2/100000))"|bc|awk '{if(length($1)==1)printf("0%s",$1);else printf("%s",$1)}'`

			if [ ! $core ]; then
				allCores=$(cat /proc/cpuinfo | grep process | awk '{print $3}')
				for core in $allCores
	    				do
       			 		status=`rdmsr -p ${core} 0x770 -f 0:0`
				        if [[ ${status} == 1 ]]; then
				            echo "Core[${core}]:HWP is enabled"
					    echo "high:$hdMaxFreq min:$hdMinFreq desire: $desireFreq"
					    wrmsr -p $core 0x774 '0x80'$desireFreq$hdMaxFreq$hdMinFreq
					    
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core are be set to "$2"KHZ, msr: $final !

				        else
				            echo "Core[${core}]:HWP is Disabled"
				        fi
				done	
			else
				IFS=',' read -r -a cores <<< "$parsed_core"
				for core in ${cores[@]}
					do
					status=`rdmsr -p $core 0x770 -f 0:0`
                                        if [[ ${status} == 1 ]]; then
                                            echo "Core[${core}]:HWP is enabled"
						
					    echo "Cores[${core}]:$hdMinFreq - $hdMaxFreq,fix frequency: $desireFreq $2 KHz"
                                            echo '0x80'$desireFreq$hdMaxFreq$hdMinFreq

					    wrmsr -p $core 0x774 '0x80'$desireFreq$hdMaxFreq$hdMinFreq
					    final=`rdmsr -p ${core} 0x774`
					    echo "Core" $core are be set to "$2"KHZ, msr: $final !
                                        else
                                            echo "Core[${core}]:HWP is Disabled"
                                        fi
 
				done
			fi
		else
			echo "please input the user specific frequency in KHZ!"
			exit 1
		fi
		shift 2
            ;;
	 -r|--rest)
	function_reset
	disable_C1E_C3_C6
	shift
	;;	
	-- )shift; break;;
        * ) echo "unkonw argument"; exit 1;;
    esac
done
