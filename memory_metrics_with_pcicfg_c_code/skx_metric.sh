#!/usr/bin/bash

#set -x
interval=1

get_ddr_freq()
{
    freq=`dmidecode  | grep 'Configured Clock Speed:' | grep -v Unknown | awk '{ print $4 }'`
    echo $freq
}

before=0
timer_start()
{
    now=`date +%s%N`
    before=$now
}

time_escaped()
{
    now=`date +%s%N`
    delta=`expr $now - $before`
    echo $delta
}

write_each_mc()
{
    reg=$1
    val=$2

    for socket in $cpu_list; do
        for channel in $channel_list; do
            dev=S"$socket"_iMC"$channel"
            setpci -s ${!dev} $reg".L="$val
        done
    done
}

read_cunter()
{
    socket=$1
    channel=$2
    counter=$3
    dev=S"$socket"_iMC"$channel"

    reg=`printf "0x%x" $((0xA0 + $counter * 8))`
    val_l=0x`setpci -s ${!dev} $reg".L"`
    reg=`printf "0x%x" $((reg + 4))`
    val_h=0x`setpci -s ${!dev} $reg".L"`

    echo $((($val_h << 32) + $val_l))
}

set_event()
{
    counter=$1
    val=$2

    for socket in $cpu_list; do
        reg=0xD8
        for channel in $channel_list; do
            dev=S"$socket"_iMC"$channel"
            reg=`printf "0x%x" $((0xD8 + $counter * 4))`
            setpci -s ${!dev} $reg".L="$val
        done
    done
}

get_counter()
{
    counter=$1

    total=0
    for socket in $cpu_list; do
        for channel in $channel_list; do
            val=`read_cunter $socket $channel $counter`
            #echo "Socket $socket Channel $channel: $val"
            total=$(($total+$val))
        done
    done

    echo $total
}


init()
{
    cpu_model=`cat /proc/cpuinfo | grep -e "model" | head -1 | awk '{print $3}'`
    
    if [ $cpu_model -eq 79 ]; then
        #bdx
        channel_list="0 1 2 3"
    
        S0_iMC0="7f:14.0"
        S0_iMC1="7f:14.1"
        S0_iMC2="7f:17.0"
        S0_iMC3="7f:17.1"
        S1_iMC0="ff:14.0"
        S1_iMC1="ff:14.1"
        S1_iMC2="ff:17.0"
        S1_iMC3="ff:17.1"
    elif [ $cpu_model -eq 85 ]; then
        #skx
        channel_list="0 1 2 3 4 5"
    
        S0_iMC0="64:0a.2"
        S0_iMC1="64:0a.6"
        S0_iMC2="64:0b.2"
        S0_iMC3="64:0c.2"
        S0_iMC4="64:0c.6"
        S0_iMC5="64:0d.2"
        #S1_iMC0="64:0a.2"
        #S1_iMC1="64:0a.6"
        #S1_iMC2="64:0b.2"
        #S1_iMC3="64:0c.2"
        #S1_iMC4="64:0c.6"
        #S1_iMC5="64:17.1"
    else
        echo "unkown machine ..."
        exit
    fi
    
    cpu_num=`lscpu | grep 'Socket(s)' | awk '{ print $2 }'`
    if [ $cpu_num -eq 1 ]; then
        cpu_list="0"
    elif [ $cpu_num -eq 2 ]; then
        cpu_list="0 1"
    else
        echo "the script does not $cpu_num sockets"
        exit
    fi
    
    # 1. set box_ctl.frz
    write_each_mc 0xF4 0x00000100
    
    # 2. enable couting for each monitor
    write_each_mc 0xD8 0x00400000
    write_each_mc 0xDC 0x00400000
    write_each_mc 0xE0 0x00400000
    write_each_mc 0xE4 0x00400000
    write_each_mc 0xE8 0x00400000
    
    # 3. select event & umask
    set_event 0 0x00440f04 #CAS_COUNT
    set_event 1 0x00440020 #RPQ_INSERTS
    set_event 2 0x00440081 #RPQ_OCCUPANCY
    #set_event 1 0x00440010 #RPQ_INSERTS
    #set_event 2 0x00440080 #RPQ_OCCUPANCY
    
    # 4. start counting by unfreezing the counters
    write_each_mc 0xF4 0x00000000
}

mem_utilization()
{
    #delta: nanoseconds
    delta=$1
    cas_counter=$2

    # Memory Utilization = CAS_COUNT * 64
    # Reference to the formal in P94 of <<SKX Uncore Programming Guide 565806 r0-30>> 
    bw=`echo "scale=3; $cas_counter * 64 * 1000000000 / $delta" | bc -l`
    # to MB/s
    bw=`echo "scale=3; $bw / 1024 / 1024" | bc -l`

    echo $bw
}

avg_latency()
{
    rpq_inserts_ctr=`get_counter 1`
    rpq_occupancy_ctr=`get_counter 2`

    if [ $rpq_inserts_ctr -eq 0 ]; then
        avg_latency="n/a"
    else
        occu0=`get_counter 2`
        inst0=`get_counter 1`
        sleep 1
        avg_latency=`echo "scale=3; ($occu0-$rpq_occupancy_ctr) / ($inst0-$rpq_inserts_ctr)" | bc -l`
        #avg_latency=`echo "scale=3; $rpq_occupancy_ctr / $rpq_inserts_ctr" | bc -l`
    fi

    echo $avg_latency
}

rpq_occupancy()
{
    #delta: nanoseconds
    delta=$1
    rpq_occupancy_ctr=$2

    #Copied Ian's comments here
    # By using the occupancy event with a threshold, we can count the number of cycles when the occupancy is above some threshold.
    # need to experiment to determine a good threshold, but I would start somewhere around 0x18

    rpq_occupancy=`echo "scale=3; $rpq_occupancy_ctr * 1000000000 / $delta" | bc -l`
    echo $rpq_occupancy
}


run()
{
    echo "mem utilization(MB/s), avg latency, occupancy"
    while true
    do
        # reset counter
        write_each_mc 0xF4 0x00000102

        timer_start
        sleep $interval
    
        delta=`time_escaped`

        # read counters
        cas_counter=`get_counter 0`
        rpq_inserts_ctr=`get_counter 1`
        rpq_occupancy_ctr=`get_counter 2`

        #caculate metrics
        mem=`mem_utilization $delta $cas_counter`
        lat=`avg_latency`
        occupancy=`rpq_occupancy $delta $rpq_occupancy_ctr`

        #echo "mem utilization(MB/s), avg latency, occupancy"
        echo      $mem,                  $lat,        $occupancy
    done
}


# main
init
run

# stop counting
write_each_mc 0xF4 0x00000100


