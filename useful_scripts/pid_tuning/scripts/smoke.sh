#50% core on S1 for HP, 50% core on S1 for  LP
HP_CORES=32-47,96-111
LP_CORES=48-63,112-127

#HP_CORES=32-50,96-114
#LP_CORES=51-63,115-127

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

	benchmark $HP_CORES hp &
	benchmark $LP_CORES lp 
	sleep 2
}

echo base
pqos -R > /dev/null 2>/dev/null
python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0 #<-ll
col 


#benchmark $LP_CORES lp

echo rdt
python2 /home/womix/hwdrc_postsi/hwdrc_config.py MCLOS_EN 0x0
pqos -R > /dev/null 2>/dev/null
pqos -a core:1=$LP_CORES > /dev/null 2>/dev/null
#pqos -e mba:0=100 > /dev/null 2>/dev/null
#pqos -e cat:0=0xfff > /dev/null 2>/dev/null

pqos -e mba:1=10 > /dev/null 2>/dev/null
#pqos -e cat:1=0xfff > /dev/null 2>/dev/null
col

echo "drc"
pqos -R
python /home/womix/hwdrc_postsi/hwdrc_config.py init 0x0

pqos -a core:4=$HP_CORES >/dev/null 2>/dev/null
pqos -a core:7=$LP_CORES >/dev/null 2>/dev/null
col
