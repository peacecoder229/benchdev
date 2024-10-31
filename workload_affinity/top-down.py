import os
import string
import re
from subprocess import Popen, PIPE
from workload_categorization import WorkloadType
from performance import clucene_performance_monitor 

event_list = {
   "CPU_CLK_UNHALTED.THREAD_ANY":"r23003c",
   "CPU_CLK_UNHALTED.THREAD":"r3003c",
   "IDQ_UOPS_NOT_DELIVERED.CORE":"r3019c",
   "IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE":"r403019c",
   "UOPS_ISSUED.ANY":"r3010e",
   "UOPS_RETIRED.RETIRE_SLOTS":"r302c2",
   "INT_MISC.RECOVERY_CYCLES_ANY":"r23010d",
   "BR_MISP_RETIRED.ALL_BRANCHES":"r300c5",
   "MACHINE_CLEARS.COUNT":"r10301c3",
   "CYCLE_ACTIVITY.STALLS_MEM_ANY":"r100310a3",
   "EXE_ACTIVITY.BOUND_ON_STORES":"r340a6",
   "EXE_ACTIVITY.1_PORTS_UTIL":"r302a6",
   "EXE_ACTIVITY.2_PORTS_UTIL":"r304a6",
   "EXE_ACTIVITY.EXE_BOUND_0_PORTS":"r301a6",
   "IDQ.MS_UOPS":"r33079",
   "INST_RETIRED.ANY":"r300c0"
}

counter_list = {
    "r23003c":0,
    "r3003c":0,
    "r3019c":0,
    "r403019c":0,
    "r3010e":0,
    "r302c2":0,
    "r23010d":0,
    "r300c5":0,
    "r10301c3":0,
    "r100310a3":0,
    "r340a6":0,
    "r302a6":0,
    "r304a6":0,
    "r301a6":0,
    "r33079":0,
    "r300c0":0
}

num_of_counter = len(counter_list)

def get_event_list():
    str_event = ''
    for i in event_list:
        str_event += event_list[i] + ','

    str_event = str_event.strip(',')  # remove last ','
    return str_event

threads = 1


if __name__ == "__main__":
    str_event = get_event_list()
    Iteration = 200 
    i = 0
    W = WorkloadType()
    cmd = "perf stat -e " + str_event + " -I 1000 -a"
    print(cmd)
    output = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    icounter = 0
    while output.poll() is None and i < Iteration:
        i += 1
        line = output.stderr.readline().strip()  ## perf output treat as stderr, not stdout

        if 'time' not in line:
            icounter += 1
            vec = re.split('\s+', line)
            evt = vec[2]
            num = float(vec[1].replace(',', ''))
            counter_list[evt] = num
            if icounter >= num_of_counter:
                CPU_CLK_UNHALTED_THREAD_ANY = counter_list[event_list["CPU_CLK_UNHALTED.THREAD_ANY"]]
                CPU_CLK_UNHALTED_THREAD = counter_list[event_list["CPU_CLK_UNHALTED.THREAD"]]
                IDQ_UOPS_NOT_DELIVERED_CORE = counter_list[event_list["IDQ_UOPS_NOT_DELIVERED.CORE"]]
                IDQ_UOPS_NOT_DELIVERED_CYCLES_0_UOPS_DELIV_CORE = counter_list[event_list["IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE"]]
                UOPS_ISSUED_ANY = counter_list[event_list["UOPS_ISSUED.ANY"]]
                UOPS_RETIRED_RETIRE_SLOTS = counter_list[event_list["UOPS_RETIRED.RETIRE_SLOTS"]]
                INT_MISC_RECOVERY_CYCLES_ANY = counter_list[event_list["INT_MISC.RECOVERY_CYCLES_ANY"]]
                BR_MISP_RETIRED_ALL_BRANCHES = counter_list[event_list["BR_MISP_RETIRED.ALL_BRANCHES"]]
                MACHINE_CLEARS_COUNT = counter_list[event_list["MACHINE_CLEARS.COUNT"]]
                CYCLE_ACTIVITY_STALLS_MEM_ANY = counter_list[event_list["CYCLE_ACTIVITY.STALLS_MEM_ANY"]]
                EXE_ACTIVITY_BOUND_ON_STORES = counter_list[event_list["EXE_ACTIVITY.BOUND_ON_STORES"]]
                EXE_ACTIVITY_1_PORTS_UTIL = counter_list[event_list["EXE_ACTIVITY.1_PORTS_UTIL"]]
                EXE_ACTIVITY_2_PORTS_UTIL = counter_list[event_list["EXE_ACTIVITY.2_PORTS_UTIL"]]
                EXE_ACTIVITY_EXE_BOUND_0_PORTS = counter_list[event_list["EXE_ACTIVITY.EXE_BOUND_0_PORTS"]]
                IDQ_MS_UOPS = counter_list[event_list["IDQ.MS_UOPS"]]
                INST_RETIRED_ANY = counter_list[event_list["INST_RETIRED.ANY"]]

                TopDown_Frontend_Bound = 100 * IDQ_UOPS_NOT_DELIVERED_CORE / (4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)
                TopDown_Frentend_Latency = 100 * IDQ_UOPS_NOT_DELIVERED_CYCLES_0_UOPS_DELIV_CORE / (CPU_CLK_UNHALTED_THREAD_ANY / threads)
                TopDown_Frentend_Bandwidth = 100 * (IDQ_UOPS_NOT_DELIVERED_CORE - 4 * IDQ_UOPS_NOT_DELIVERED_CYCLES_0_UOPS_DELIV_CORE) / (4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)
                TopDown_BadSpeculation_Bound = 100 * (UOPS_ISSUED_ANY - UOPS_RETIRED_RETIRE_SLOTS + (4 * INT_MISC_RECOVERY_CYCLES_ANY / threads)) / (4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)
                TopDown_BadSpeculation_BranchMisp = ( BR_MISP_RETIRED_ALL_BRANCHES /( BR_MISP_RETIRED_ALL_BRANCHES + MACHINE_CLEARS_COUNT) ) * 100 * \
                                     (UOPS_ISSUED_ANY - UOPS_RETIRED_RETIRE_SLOTS + 4 * INT_MISC_RECOVERY_CYCLES_ANY / threads) / ( 4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)

                TopDown_BadSpeculation_MachineClears = ( MACHINE_CLEARS_COUNT / (MACHINE_CLEARS_COUNT + BR_MISP_RETIRED_ALL_BRANCHES) ) * 100 * \
                                        (UOPS_ISSUED_ANY - UOPS_RETIRED_RETIRE_SLOTS + 4 * INT_MISC_RECOVERY_CYCLES_ANY / threads) / ( 4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)

                TopDown_Backend_bound = 100 - (100 * (UOPS_ISSUED_ANY - UOPS_RETIRED_RETIRE_SLOTS + 4 * INT_MISC_RECOVERY_CYCLES_ANY/ threads + IDQ_UOPS_NOT_DELIVERED_CORE + UOPS_RETIRED_RETIRE_SLOTS)) / \
                       (4 * CPU_CLK_UNHALTED_THREAD_ANY / threads)

                t2 = 0
                if INST_RETIRED_ANY / CPU_CLK_UNHALTED_THREAD > 1.8:
                    t2 = EXE_ACTIVITY_2_PORTS_UTIL
                t0 = 100 * (1 - ((UOPS_ISSUED_ANY - UOPS_RETIRED_RETIRE_SLOTS + 4 * (INT_MISC_RECOVERY_CYCLES_ANY / threads) + IDQ_UOPS_NOT_DELIVERED_CORE + UOPS_RETIRED_RETIRE_SLOTS) / (4 * CPU_CLK_UNHALTED_THREAD_ANY/threads)))
                t1 = (CYCLE_ACTIVITY_STALLS_MEM_ANY + EXE_ACTIVITY_BOUND_ON_STORES) / (EXE_ACTIVITY_EXE_BOUND_0_PORTS + EXE_ACTIVITY_1_PORTS_UTIL + t2 + CYCLE_ACTIVITY_STALLS_MEM_ANY + EXE_ACTIVITY_BOUND_ON_STORES)

                TopDown_Backend_Memory = t0 * t1
                TopDown_Backend_Core = t0 * (1 - t1)

                t0 = (UOPS_RETIRED_RETIRE_SLOTS / (4 * (CPU_CLK_UNHALTED_THREAD_ANY / threads)))
                print(UOPS_ISSUED_ANY, CPU_CLK_UNHALTED_THREAD_ANY)
                t1 = (UOPS_RETIRED_RETIRE_SLOTS / UOPS_ISSUED_ANY) * IDQ_MS_UOPS / (4 * (CPU_CLK_UNHALTED_THREAD_ANY / threads))
                TopDown_Retiring = 100 * t0
                TopDown_Retiring_Base = 100 * (t0 - t1)
                TopDown_Retiring_Microcode_Sequencer = 100 * ( (UOPS_RETIRED_RETIRE_SLOTS/UOPS_ISSUED_ANY) * IDQ_MS_UOPS) / (4 * (CPU_CLK_UNHALTED_THREAD_ANY / threads))

                print("----------------------------------------------------")
                print("TopDown_Frontend_Bound: %.4f%%" % TopDown_Frontend_Bound)
                print("..TopDown_Frentend_Latency: %.4f%%" % TopDown_Frentend_Latency)
                print("..TopDown_Frentend_Bandwidth: %.4f%%\n" % TopDown_Frentend_Bandwidth)

                print("TopDown_BadSpeculation_Bound: %.4f%%" % TopDown_BadSpeculation_Bound)
                print("..TopDown_BadSpeculation_BranchMisp: %.4f%%" % TopDown_BadSpeculation_BranchMisp)
                print("..TopDown_BadSpeculation_MachineClears: %.4f%%\n" % TopDown_BadSpeculation_MachineClears)

                print("TopDown_Backend_bound: %.4f%%" % TopDown_Backend_bound)
                print("..TopDown_Backend_Memory: %.4f%%" % TopDown_Backend_Memory)
                print("..TopDown_Backend_Core: %.4f%%\n" % TopDown_Backend_Core)

                print("TopDown_Retiring: %.4f%%" % TopDown_Retiring)
                print("..TopDown_Retiring_Base: %.4f%%" % TopDown_Retiring_Base)
                print("..TopDown_Retiring_Microcode_Sequencer: %.4f%%\n" % TopDown_Retiring_Microcode_Sequencer)

                icounter = 0
                PM = clucene_performance_monitor()
                clucene_p = PM.return_performance()
                #W.feed_data(TopDown_Frontend_Bound, TopDown_Frentend_Latency)
                W.feed_data(TopDown_Frontend_Bound, clucene_p)
                print clucene_p
    W.resort()
    print W.get_result()
    print W.find_flat()
    exit()
