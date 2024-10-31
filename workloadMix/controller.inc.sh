
function initial_settings()
{
	
	wrmsr -p 24 0x150 0x8000001980000000

	pkill -9 python
	pqos -R
}

function set_hwdrc()
{

	
	initial_settings

	wrmsr -p 24 0x150 0x8000001600000700
	wrmsr -p 24 0x150 0x80000017810f04FF
	wrmsr -p 24 0x150 0x8000001780010000
	wrmsr -p 24 0x150 0x8000001881800104
	wrmsr -p 24 0x150 0x8000001980000001
	
	pqos -a llc:4=$HP_CORES 
	pqos -a llc:5=$LP_CORES
	
	pqos -e llc:5=$DEFAULT_CAT 
}

function set_swdrc()
{
	initial_settings

	pqos -a llc:1=$LP_CORES 
	
	pqos -e mba:1=10 
	pqos -e llc:1=$DEFAULT_CAT 
	
	cd /pnpdata/dynamic_resource_control
	taskset -c 0-27 python starter.py imc_config.json &
	cd - 
}

function set_rdt()
{

	initial_settings

	pqos -a llc:1=$LP_CORES 

	pqos -e llc:1=$DEFAULT_CAT
	pqos -e mba:1=10 
}

function run_hp()
{
	data_folder=$2/hp
	workload=$1

	mkdir -p $data_folder

	$workload $HP_CORES $data_folder
}

function run_lp()
{
	data_folder=$2/lp
	workload=$1

	mkdir -p $data_folder

	$workload $LP_CORES $data_folder & 
}
