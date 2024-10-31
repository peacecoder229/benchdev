#HP_CORES=32-47,96-111
#LP_CORES=48-63,112-127

#HP_CORES=$1
#LP_CORES=48-63,112-127

#D1
#HPCORES=24-35,72-83
#LPCORES=36-47,84-95

if [ $# -eq 0 ]; then
HP_CORES=24-35,72-83
else
HP_CORES=$1
fi

LP_CORES=36-47,84-95

TIME=5

function benchmark()
{
        core=$1
        tag=$2
        score=$(mlc --loaded_latency -R -t${TIME} -T -k${core} -d0 | grep 00000 | awk '{print $3}')

        echo ============${tag} = ${score}===============
}

function col()
{

        benchmark $LP_CORES lp &
        benchmark $HP_CORES hp
        #sleep 2
}

function stream_test()
{
        cores=$1
        tag=$2
        score=`taskset -c ${cores} /home/longcui/benchmark/stream/stream_c_200times|grep Triad | awk '{print $2}'`
        echo ============${tag} = ${score}===============
}

echo "HP_CORES="$HP_CORES
echo "LP_CORES="$LP_CORES

echo "====MLC LP only===="
benchmark $LP_CORES lp

echo "====MLC HP only===="
benchmark $HP_CORES hp

echo "====stream LP only===="
stream_test $LP_CORES lp 

echo "====stream HP only===="
stream_test $HP_CORES hp 

echo "====MLC HP+LP mix===="
col
