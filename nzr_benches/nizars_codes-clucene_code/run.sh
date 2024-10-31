#!/bin/bash

if [ -z "$1"]
then
    echo "Please enter test name"
    exit 1
else
    cd /pnpdata/clucene_benchmark_new/emon/results/
    rm -rf *.dat
    rm -rf *.out
    cd /pnpdata/clucene_benchmark_new/src/benchmark-dev/clucene_search_main/

    /pnpdata/hwpdesire/hwpdesire.sh -a 2700000
    /pnpdata/hwpdesire/hwpdesire.sh -m 2700000
    wrmsr 0x620 0xc14

    python3 experiment.py 30 4 0-15,32-47 750 hw2p7 1 all u ../index_big_uncompressed

    sleep 15

    #/pnpdata/hwpdesire/hwpdesire.sh -a 2700000
    #/pnpdata/hwpdesire/hwpdesire.sh -m 2700000
    #wrmsr 0x620 0xc14

    python3 experiment.py 30 4 0-15,32-47 750 hw2p7 1 t l ../index_big_uncompressed

    cd /pnpdata/EDPprocess/edp_linux/edp-v3.6
    ./process_ruby_edp.py /pnpdata/clucene_benchmark_new/emon/results/ /pnpdata/clucene_benchmark_new/emon/results/edp/$1/ /pnpdata/EDPprocess/skx-2s.xml 0

    cd /pnpdata/EDPprocess/
    ./process_socktview_rev2.py /pnpdata/clucene_benchmark_new/emon/results/edp/$1/ /pnpdata/clucene_benchmark_new/emon/results/edp/$1/runT_sock_sum.csv all_metric

fi
