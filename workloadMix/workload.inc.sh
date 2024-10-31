
setenforce 0


function specjbb()
{
	cpu_set=$1
	result_path=$2
	docker run --rm --cpuset-cpus=$cpu_set --cpuset-mems=0 -e WAREHOUSE=$HP_INSTANCE -v `pwd`/$result_path:/results specjbb:quick 
}

function bwaves()
{

	cpu_set=$1
	result_path=$2
	docker run --rm --cpuset-cpus=$cpu_set --cpuset-mems=0  -v `pwd`/$result_path:/SPECcpu/result -e INSTANCES=$LP_INSTANCE -e WORKLOAD=bwaves_s speccpu2017:latest
}

function clucene()
{
	cpu_set=$1
	result_path=$2

	if [ $cpu_set == $HP_CORES ]
	then	
		docker run --rm -v /index/index_wiki_interleaved:/index_0:z -v /index/index_wiki_interleaved1:/index_1:z --cpuset-cpus=$cpu_set --cpuset-mems=0  -e  TOPK=20 -e THREAD=24 -e DURATION=6  clucene:io > $result_path/clucene.out 
	else
		docker run --rm -v /index/index_wiki_interleaved3:/index_0:z -v /index/index_wiki_interleaved2:/index_1:z --cpuset-cpus=$cpu_set --cpuset-mems=0  -e  TOPK=20 -e THREAD=24 -e DURATION=6  clucene:io > $result_path/clucene.out 
	fi
}

function rn50()
{
	cpu_set=$1
	result_path=$2
	
	docker run --rm --cpuset-cpus=$cpu_set --cpuset-mems=0  -e OMP_NUM_THREADS=24 mxnet_benchmark >$result_path/mx-jbb.out 

}

function widedeep()
{
	cpu_set=$1
	result_path=$2

	docker run --rm --cpuset-cpus=$cpu_set --cpuset-mems=0 --privileged widedeep >$result_path/widedeep.out 
}

function speccpu2006()
{
	cpu_set=$1
	result_path=$2
	
	comp=$3

	docker run --rm --cpuset-cpus=$cpu_set --cpuset-mems=0  -v `pwd`/$result_path:/SPECcpu/result  -e INSTANCES=24 -e WORKLOAD=$comp speccpu2006:latest 

}

function _bwaves()
{
	speccpu2006 $1 $2 bwaves
}

function perlbench()
{
	speccpu2006 $1 $2 perlbench
}

function povray()
{
	speccpu2006 $1 $2 povray
}

function leslie3d()
{
	speccpu2006 $1 $2 leslie3d
}


function libquantum()
{
	speccpu2006 $1 $2 libquantum
}
