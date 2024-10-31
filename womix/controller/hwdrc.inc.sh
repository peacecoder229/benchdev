HP_COS=4
LP_COS=7

function initial_settings()
{
	# reset_cpu_frequency
	# wrmsr -p 24 0x150 0x8000001980000000
	python2 hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 
	# pkill -9 python
	reset_rdt
}


function set_hwdrc()
{
	
	initial_settings

	# wrmsr -p 24 0x150 0x8000001600000700
	# wrmsr -p 24 0x150 0x80000017810f04FF
	# wrmsr -p 24 0x150 0x8000001780010000
	# wrmsr -p 24 0x150 0x8000001881800104
	# wrmsr -p 24 0x150 0x8000001980000001

	python2 hwdrc_postsi/hwdrc_config.py init 0 
    python2 hwdrc_postsi/hwdrc_config.py init 0 # enable twice as work around
	# $! != 0  exit;
	
	pqos -a llc:$HP_COS=$HP_CORES 
	pqos -a llc:$LP_COS=$LP_CORES
	
	# pqos -e llc:$LP_COS=$LP_CAT
	# pqos -e mba:$LP_COS=$LP_MBA 
}

function set_swdrc()
{
	initial_settings

	pqos -a llc:$LP_COS=$LP_CORES 
	
	pqos -e mba:$LP_COS=$LP_MBA 
	pqos -e llc:$LP_COS=$LP_CAT 
	
	cd /root/lc/dynamic_resource_control
	taskset -c 1-23 python starter.py imc_config.json &
	cd - 
}

function reset_rdt()
{
	pqos -R
}

function set_rdt()
{

	initial_settings

	pqos -a llc:$LP_COS=$LP_CORES 

	pqos -e llc:$LP_COS=$LP_CAT
	pqos -e mba:$LP_COS=$LP_MBA 

	pqos -a llc:$HP_COS=$HP_CORES
}

function rdt_debug()
{
	path=$1
	pqos -s > $path/rdt_status.log
}

function hwdrc_debug()
{
	 path=$1
	 
	 mkdir -p $path
	 python2 hwdrc_config.py reg_dump 0 > $path/hwdrc_status.log
}
