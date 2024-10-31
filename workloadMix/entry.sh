#!/bin/bash 

source ./test_process.inc.sh 
# enable emon here
#source ./emon.inc.sh

HP_CORES=24-35,72-83
LP_CORES=36-47,84-95

DEFAULT_CAT=0x7ff

./hwpdesire.sh -f 2100000

initial_settings
full_colocation "mix"

set_rdt
full_colocation "mba_only"

set_swdrc
full_colocation "swdrc"

set_hwdrc
full_colocation "hwdrc"
