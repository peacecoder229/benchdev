#!/bin/bash 

source ./test_process.inc.sh 
# enable emon here
#source ./emon.inc.sh

HP_CORES=0-13
LP_CORES=14-27

DEFAULT_CAT=0x7ff

./hwpdesire.sh -f 2100000

initial_settings
full_colocation "mix"

set_swdrc
full_colocation "swdrc"
