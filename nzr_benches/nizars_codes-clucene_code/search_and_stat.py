import sys,os
import numpy as np
import matplotlib
import time

matplotlib.use('Agg')

out = open("results.txt", "a")
out.write("test_name, hwptag, topk, thread, core, time, QPS, average_latency, Total_QPS\n")

from matplotlib import pyplot as plt

os.system('rm -f log_*.log')

if len(sys.argv) != 7:
    #28 4 0-27 400 2000 
    print('usage: python3 %s thread_number time_for_run(min) cpu_list topk hwptag test_name' % sys.argv[0])
    sys.exit()

nthreads = int(sys.argv[1])
time_dur = int(sys.argv[2])
cpu_list = str(sys.argv[3])
topk = int(sys.argv[4])
hwptag = str(sys.argv[5])
test_name = str(sys.argv[6])
###print('nthreads: %d, run time: %d, cpu_list: %s test_name: %s' %(nthreads, time_dur, cpu_list))

time_start = float(time.time())
out.write(test_name + ", " + hwptag + str(topk) + ", " + str(nthreads) + ", " + cpu_list + ", " +  str(time_dur) + ", ")

#prepare for emon
emonname = "runT-" + str(nthreads) + "tm-" + str(time_dur) + "c-" + cpu_list + "tk-" + str(topk) + "hwp_" + hwptag
#os.system("source /pnpdata/clucene_benchmark_new/emon/run_emon.sh " + emonname)
lib="LD_LIBRARY_PATH=/lib64:$LD_LIBRARY_PATH"
cmd = '%s numactl -C  %s  ./main_searcher %d %d %d %s' % (lib, cpu_list, nthreads, time_dur, topk, test_name)
print('run cmd: %s'%cmd)
os.system(cmd)
time_end = float(time.time())

print('search run finished')
#os.system("source /opt/intel/sep/sep_vars.sh ; emon -stop")

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

