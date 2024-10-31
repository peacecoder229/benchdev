setenforce 0

function empty()
{
	sleep 0
}

function fake()
{
	echo "Should run $3 instances on core $1" > $2/just.log
}

function stream_omp()
{
	cpuset=$1
	result_path=$2
	ins=$3
	name=$4

	docker run --rm --cpuset-cpus=$cpu_set --name=$name  -e OMP_NUM_THREADS=1=$ins stream_omp > $result_path/steam.out
}

function specjbb()
{
	cpu_set=$1
	result_path=$2

	ins=$3
	name=$4

	docker run --rm --cpuset-cpus=$cpu_set --name=$name  --name=$name  -e WAREHOUSE=$ins -v `pwd`/$result_path:/results specjbb:quick 
}


function clucene()
{
	cpu_set=$1
	result_path=$2
	ins=$3
	name=$4

	if [ $cpu_set == $HP_CORES ] # for HWDRC multiple instance
	then	
		docker run --rm -v /index/index_wiki_interleaved:/index_0:z -v /index/index_wiki_interleaved1:/index_1:z --cpuset-cpus=$cpu_set --name=$name  -e  TOPK=20 -e THREAD=$ins -e DURATION=6  clucene:io > $result_path/clucene.out 
	else
		docker run --rm -v /index/index_wiki_interleaved3:/index_0:z -v /index/index_wiki_interleaved2:/index_1:z --cpuset-cpus=$cpu_set --name=$name  -e  TOPK=20 -e THREAD=$ins -e DURATION=6  clucene:io > $result_path/clucene.out 
	fi
}

function rn50()
{
	cpu_set=$1
	result_path=$2
	ins=$3
	name=$4

	docker run --rm --cpuset-cpus=$cpu_set --name=$name  -e OMP_NUM_THREADS=$ins mxnet_benchmark 2> $result_path/rn50.out

}

function widedeep()
{
	cpu_set=$1
	result_path=$2
	ins=$3
	name=$4
	## need to fig instance numbers
	docker run --rm --cpuset-cpus=$cpu_set --name=$name  --privileged widedeep > $result_path/widedeep.out 2> $result_path/widedeep_err.out
}

function speccpu2006()
{
	cpu_set=$1
	result_path=$2
	ins=$3

	comp=$4
	name=$5

	docker run --rm --cpuset-cpus=$cpu_set --name=$name  -v `pwd`/$result_path:/SPECcpu/result  -e INSTANCES=$ins -e WORKLOAD=$comp speccpu2006:latest 

}

function speccpu2017()
{

	cpu_set=$1
	result_path=$2
	ins=$3

	comp=$4
	name=$5

	docker run --rm --cpuset-cpus=$cpu_set --name=$name  -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=$ins -e WORKLOAD=$comp speccpu2017:latest
}

# workloads from SPECcpu2006
function bwaves()
{
	speccpu2006 $1 $2 $3 bwaves $4
}

function perlbench()
{
	speccpu2006 $1 $2 $3 perlbench $4
}

function povray()
{
	speccpu2006 $1 $2 $3 povray $4
}

function leslie3d()
{
	speccpu2006 $1 $2 $3 leslie3d $4
}


function libquantum()
{
	speccpu2006 $1 $2 $3 libquantum $4
}

## workloads from SPECcpu2017
function bwaves_s()
{
        speccpu2017 $1 $2 $3 bwaves_s $4
}

function cactuBSSN_s()
{
        speccpu2017 $1 $2 $3 cactuBSSN_s $4
}

function namd_s()
{
        speccpu2017 $1 $2 $3 namd_s $4
}

function parest_s()
{
        speccpu2017 $1 $2 $3 parest_s $4
}

function povray_s()
{
        speccpu2017 $1 $2 $3 povray_s $4
}
function lbm_s()
{
        speccpu2017 $1 $2 $3 lbm_s $4
}
function wrf_s()
{
        speccpu2017 $1 $2 $3 wrf_s $4
}
function blender_s()
{
        speccpu2017 $1 $2 $3 blender_s $4
}
function cam4_s()
{
        speccpu2017 $1 $2 $3 cam4_s $4
}
function imagick_s()
{
        speccpu2017 $1 $2 $3 imagick_s $4
}
function nab_s()
{
        speccpu2017 $1 $2 $3 nab_s $4
}
function fotonik3d_s()
{
        speccpu2017 $1 $2 $3 fotonik3d_s $4
}

function roms_s()
{
        speccpu2017 $1 $2 $3 roms_s $4
}
function perlbench_s()
{
        speccpu2017 $1 $2 $3 perlbench_s $4
}
function gcc_s()
{
        speccpu2017 $1 $2 $3 gcc_s
}
function mcf_s()
{
        speccpu2017 $1 $2 $3 mcf_s $4
}

function omnetpp_s()
{
        speccpu2017 $1 $2 $3 omnetpp_s $4
}
function xalancbmk_s()
{
        speccpu2017 $1 $2 $3 xalancbmk_s $4
}
function x264_s()
{
        speccpu2017 $1 $2 $3 x264_s $4
}
function deepsjeng_s()
{
        speccpu2017 $1 $2 $3 deepsjeng_s $4
 }
function leela_s()
{
        speccpu2017 $1 $2 $3 leela_s $4
}
function exchange2_s()
{
        speccpu2017 $1 $2 $3 exchange2_s $4
}
function xz_s()
{
        speccpu2017 $1 $2 $3 xz_s $4
}
function pop2_s()
{
        speccpu2017 $1 $2 $3 pop2_s $4
}

function wrk()
{
	cpu_set=$1
	result_path=$2
	ins=$3

	comp=$4
	name=$5
	#   -e NGINX_CORE=16 -e WRK_THREAD=64 -e CONNECTION=16000 -e DRUATION=120 -e RATE=680000

	docker run --rm --cpuset-cpus=$cpu_set --name=$name -e NGINX_CORE=$ins -e WRK_THREAD=64 -e CONNECTION=16000 -e DRUATION=300 -e RATE=680000 wrk > $result_path/nginx_wrk.log
}

function ffmpeg()
{
	# need to validate
	
	cpu_set=$1
	result_path=$2
	ins=$3

	comp=$4
	name=$5

	docker run --name $name --cpuset-cpus=$cpu_set -v /home/longcui/benchmark/nginx_wrk/mp4:/root/mp4  ffmepg_eric:v1 /root/mp4/run_nginx.sh > $result_path/ffmpeg.log
}