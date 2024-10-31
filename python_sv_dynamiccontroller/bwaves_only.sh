. ./shrc
. ./numa-detection.sh
ulimit -s unlimited
a=`cat /proc/cpuinfo | grep processor | wc -l`
rm -rf topo.txt
specperl nhmtopology.pl
b=`cat topo.txt`
c=`expr $a / 2`
echo "****************************************************************"
echo Running rate with $a copies on an AVX2 system with a topology of $b
echo "****************************************************************"
numactl --physcpubind=+0-13 runspec -n 1 --define default-platform-flags --    rate 14 -c cpu2006-1.2-ic16.0-lin64-ws-avx2-rate-20150812.cfg --define core    s=14 --define drop_caches --define THP_enabled -o asc -T base --no-reportab    le bwaves