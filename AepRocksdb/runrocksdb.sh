#!/bin/bash
#cores basically is total HT and hpt is HT per socket



hypt="off"
lcore=$1
#db="${2}\/${3}"
db=${2}
echo "DB is ${db}"
if [ $hypt = "on" ]
then
        highg=$(echo $lcore | cut -f2 -d,)
        lowg=$(echo $lcore | cut -f1 -d,)
        phyc_hi=$(echo $lowg | cut -f2 -d-)
        phyc_lo=$(echo $lowg | cut -f1 -d-)
        ht_hi=$(echo $highg | cut -f2 -d-)
        ht_lo=$(echo $highg | cut -f1 -d-)
        total=$(( ht_hi-ht_lo+phyc_hi-phyc_lo+2 ))
        ht=$(( total/4 ))
        i=$phyc_lo
        j=$ht_lo
else
        phyc_hi=$(echo $lcore | cut -f2 -d-)
        phyc_lo=$(echo $lcore | cut -f1 -d-)
        total=$(( phyc_hi-phyc_lo+1 ))
        ht=$(( total ))
        i=$phyc_lo
        j=$phyc_hi
fi



file=${!#}

		cd /root/AepRocksdb/
		cp 16T_mmap ${file}_${i}-${j}
		#cp 16T_mmap_3db ${file}_${stc}-${edc}
		sed -i "s/THREADS: [0-9]*/THREADS: ${ht}/" ${file}_${i}-${j}
		sed -i "s/DURATION: [0-9]*/DURATION: 300/"  ${file}_${i}-${j}
		sed -i "s/DB: \/rockspmem/DB: \/${db}/" ${file}_${i}-${j}
		echo "numactl --membind=0 --physcpubind=${i}-${j} ./db_bench.py ${file}_${i}-${j} &"
		numactl --membind=0 --physcpubind=${i}-${j} ./db_bench.py ${file}_${i}-${j} &
		pids[${i}]=$!
		#/root/QoS_scripts/collect_metric.sh ${file} rock &
		runname[${i}]=${file}_${i}-${j}
		sleep 1
		cd -
		shift
		shift
		shift

for pid in ${pids[*]}; do
		echo $pid
	    wait $pid
    done
   
echo "All rocksdb runs complete!!!"

sleep 1

for tag in ${runname[*]}; do
	cd /root/AepRocksdb/results
	run=$(echo $tag | awk -F_ '{print $3 " " $4 " " $5}')
	#res=$(cat $tag/${tag}_res.csv | grep "^1," | awk -F, '{printf("%s %s %s %s %s\n", $22, $23, $24, $25, $26)}')
	res=$(cat $tag/${tag}_res.csv | grep "^1," | awk -F, '{printf("%s %s %s %s %s %s %s %s %s\n", $22, $23, $24, $25, $26, $12, $13, $17, $16)}')
	cd -
	#echo "cat mba cores p50 p75 p90 p99 p999" > ${tag}
	echo "p50 p75 p90 p99 p999 thread microspops avg_lat totalcount" > ${tag}
	echo "${res}" >> ${tag}
	#cp -f  ${tag}  /root/QoS_scripts/

done
sleep 1
touch ${file}_rockdbonly.txt

paste ${runname[*]} >> ${file}_rockdbonly.txt
rm -f ${runname[*]}




#cat result/*intrate.refrate.txt | grep "mcf.*${core}\|xz.*${core}\|x264.*${core}\|deepsjeng.*${core}" > ${file}.txt
