
function set_cos_rdt()
{
	cpuset=$1
	cos=$2

	cat=$3
	mba=$4
	
	cat_mask=$(echo "obase=16;2^${cat} -1" | bc  )
	pqos -a llc:$cos=$cpuset 

	pqos -e llc:$cos=0x$cat_mask
	pqos -e mba:$cos=$mba
}

function set_cpu_frequency()
{
	core=$1
	freq=$2

	./tool/hwpdesire.sh -c $core -f ${freq}00000
}

function set_all_cpu_frequency()
{
	freq=$1

	./tool/hwpdesire.sh -f ${freq}00000
}

function reset_cpu_frequency()
{
	./tool/hwpdesire.sh -r
}

function uncore_frequency()
{
	ufreq=$1
	hex_ufreq=$( echo "obase=16;${ufreq}" | bc )

	wrmsr -a 0x620  0x${hex_ufreq}${hex_ufreq}   
}
