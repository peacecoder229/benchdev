import sys,os
import numpy as np
import matplotlib
import time

matplotlib.use('Agg')
from matplotlib import pyplot as plt

if len(sys.argv) != 10:
	#16 4 0-15 400 2000
	print('usage: python3 %s thread_number time_for_run(min) cpu_list topk hwptag num_tests test_name(t,c,tc,tpc,all) log(l,u) index_file_dir' % sys.argv[0])
	sys.exit()

nthreads = int(sys.argv[1])
time_dur = int(sys.argv[2])
cpu_list = str(sys.argv[3])
topk = int(sys.argv[4])
hwptag = str(sys.argv[5])
num_tests = int(sys.argv[6])
test_name = str(sys.argv[7])
log = str(sys.argv[8])
index_file_dir = str(sys.argv[9])

out = open("results.txt", "a")
out.write("Experiment - " + index_file_dir + ":\n")
out.write("test_name, log, hwptag, topk, thread, core, time, QPS, average_latency, Total_QPS\n")
out.flush()

def search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, test_name):
	os.system('rm -rf log_*.log');
	
	time_start = float(time.time())
	out.write(test_name + ", " + log + ", " + hwptag + str(topk) + ", " + str(nthreads) + ", " + cpu_list + ", " +  str(time_dur) + ", ")

	#prepare for emon
	emonname = "runT-" + str(nthreads) +  "c-" + cpu_list + "tk-" + str(topk) + "hwp_" + hwptag + "nm_" + test_name + "_" + log
	os.system("source /pnpdata/clucene_benchmark_new/emon/run_emon.sh " + emonname)
	lib="LD_LIBRARY_PATH=/lib64:$LD_LIBRARY_PATH"
	if log == 'l':
		cmd = '%s numactl -C  %s  ./main_searcher %d %d %d %s %s' % (lib, cpu_list, nthreads, time_dur, topk, test_name, index_file_dir)
	elif log == 'u':
		cmd = '%s numactl -C  %s  ./main_searcher_unlogged %d %d %d %s %s' % (lib, cpu_list, nthreads, time_dur, topk, test_name, index_file_dir)
	else:
		print('Error')
		sys.exit()

	print('run cmd: %s'%cmd)
	os.system(cmd)
	time_end = float(time.time())

	print('search run finished')
	os.system("source /opt/intel/sep/sep_vars.sh ; emon -stop")

	os.system('grep \'Search took(us):\' log_*.log > analysis_log')

	latency = []

	with open('analysis_log') as fp:
		for line in fp:
			line = line.strip('\n')
			vec = line.split(' ')
			latency.append(float(vec[-1]))

	qps =  len(latency) / (time_end - time_start)

	average_latency = np.mean(latency)

	stat_latency_lt_30 = 0
	stat_latency_lt_50 = 0
	stat_latency_lt_70 = 0
	stat_latency_lt_100 = 0
	stat_latency_lt_150 = 0
	stat_latency_lt_200 = 0
	print('collect stats of latency')

	for i in latency:
		if i > 30000:
			stat_latency_lt_30 += 1
			if i > 50000:
				stat_latency_lt_50 += 1
				if i > 70000:
					stat_latency_lt_70 += 1
					if i > 100000:
						stat_latency_lt_100 += 1
						if i > 150000:
							stat_latency_lt_150 += 1
							if i > 200000:
								stat_latency_lt_200 += 1





	plt.plot(latency, '.')
	plt.savefig('latency_distribution.png')

	print('QPS: %.2f, average_latency(us): %.2f' % (qps, average_latency))

	print('total qps %d: ' % len(latency))

	out.write(str(qps) + ", " + str(average_latency) + ", " +  str(len(latency)) + "\n")
	print('number of latency > 30000(us): %d, take: %.2f %% ' % (stat_latency_lt_30, stat_latency_lt_30 * 100.0/len(latency)))
	print('number of latency > 50000(us): %d, take: %.2f %% ' % (stat_latency_lt_50, stat_latency_lt_50 * 100.0/len(latency)))
	print('number of latency > 70000(us): %d, take: %.2f %% ' % (stat_latency_lt_70, stat_latency_lt_70 * 100.0/len(latency)))
	print('number of latency > 100000(us): %d, take: %.2f %% ' % (stat_latency_lt_100, stat_latency_lt_100 * 100.0/len(latency)))
	print('number of latency > 150000(us): %d, take: %.2f %% ' % (stat_latency_lt_150, stat_latency_lt_150 * 100.0/len(latency)))
	print('number of latency > 200000(us): %d, take: %.2f %% ' % (stat_latency_lt_200, stat_latency_lt_200 * 100.0/len(latency)))
	out.write("lat > 200ms = " + str(stat_latency_lt_200) + " test: " + emonname + "\n")
	out.flush()
	return (qps, average_latency)

t_qps_sum = 0
t_lat_sum = 0
c_qps_sum = 0
c_lat_sum = 0
tc_qps_sum = 0
tc_lat_sum = 0
tpc_qps_sum = 0
tpc_lat_sum = 0
tct_qps_sum = 0
tct_lat_sum = 0

if test_name == 't' or test_name == 'all':
	for x in range(0, num_tests):
		(temp_qps, temp_lat) = search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, 't')
		t_qps_sum += temp_qps
		t_lat_sum += temp_lat

if test_name == 'c' or test_name == 'all':
	for x in range(0, num_tests):
		(temp_qps, temp_lat) = search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, 'c')
		c_qps_sum += temp_qps
		c_lat_sum += temp_lat

if test_name == 'tc' or test_name == 'all':
	for x in range(0, num_tests):
		(temp_qps, temp_lat) = search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, 'tc')
		tc_qps_sum += temp_qps
		tc_lat_sum += temp_lat

if test_name == 'tpc' or test_name == 'all':
	for x in range(0, num_tests):
		(temp_qps, temp_lat) = search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, 'tpc')
		tpc_qps_sum += temp_qps
		tpc_lat_sum += temp_lat

if test_name == 'tct' or test_name == 'all':
	for x in range(0, num_tests):
		(temp_qps, temp_lat) = search_and_stat(nthreads, time_dur, cpu_list, topk, hwptag, 'tct')
		tct_qps_sum += temp_qps
		tct_lat_sum += temp_lat


out.write("\nResult Averages of %d Tests" % num_tests)

if log == 'l':
	out.write(" (Logged)\n")
elif log == 'u':
	out.write(" (Unlogged)\n")
else:
	out.write("\n")

if test_name == 't' or test_name == 'all':
	out.write("Title Search: QPS - %s, Average Latency(us) - %s\n" % (str(t_qps_sum/num_tests), str(t_lat_sum/num_tests)))

if test_name == 'c' or test_name == 'all':
	out.write("Contents Search: QPS - %s, Average Latency(us) - %s\n" % (str(c_qps_sum/num_tests), str(c_lat_sum/num_tests)))

if test_name == 'tc' or test_name == 'all':
	out.write("Title-Contents Search: QPS - %s, Average Latency(us) - %s\n" % (str(tc_qps_sum/num_tests), str(tc_lat_sum/num_tests)))

if test_name == 'tpc' or test_name == 'all':
	out.write("Title-Phrased-Contents Search: QPS - %s, Average Latency(us) - %s\n" % (str(tpc_qps_sum/num_tests), str(tpc_lat_sum/num_tests)))

if test_name == 'tct' or test_name == 'all':
	out.write("Title-Contents-Time Search: QPS - %s, Average Latency(us) - %s\n" % (str(tct_qps_sum/num_tests), str(tct_lat_sum/num_tests)))

out.write("\n\n");
out.close()
