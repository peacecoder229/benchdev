cd /pnpdata/clucene_benchmark_new/emon/results/

cd /pnpdata/EDPprocess/edp_linux/edp-v3.6
./process_ruby_edp.py /pnpdata/clucene_benchmark_new/emon/results/ /pnpdata/clucene_benchmark_new/emon/results/edp/$1/ /pnpdata/EDPprocess/skx-2s.xml 0

cd /pnpdata/EDPprocess/
./process_socktview_rev2.py /pnpdata/clucene_benchmark_new/emon/results/edp/$1/ /pnpdata/clucene_benchmark_new//emon/results/edp/$1/runT_sock_sum.csv all_metric
