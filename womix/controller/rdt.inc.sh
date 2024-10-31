
HP_COS=4
LP_COS=5

HP_CAT=0xfff
HP_MBA=100

function initial_settings()
{
	reset_cpu_frequency

	pkill -9 python
	reset_rdt
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
	pqos -e llc:$HP_COS=$HP_CAT
	pqos -e mba:$HP_COS=$HP_MBA
}

# source controller/freq.inc.sh
