
sv.refresh()
import pm.pmdebug as d
d.general.load_pcode_debug_vars(r"/root/icx_microcode/20210316_8d710210_21ww04f_timewindow_distribution_fix_sync_with_latest_change_x32_remove_fuse_v2/pcode.dbg.gz")

import time
import sys
import csv
import os
import subprocess
import svtools.logging.toolbox as tool

path = "/root/pid_scaling/"
def pid_scaling(p, i, d, sp):

    set_point(sp)
    sv.socket0.pcudata.mclos_pid_struct_kp = p
    sv.socket0.pcudata.mclos_pid_struct_ki = i
    sv.socket0.pcudata.mclos_pid_struct_kd = d
    # sv.socket0.pcudata.mclos_pid_struct_kd = d
    #set_point(sp)
    # os.exec(./hwdrc_change_setpoint.sh 80)
    global path

    csvName="%s_%s_%s_%s.csv" % (p,i,d,sp)
    csvName = os.path.join(path, csvName)

    log=tool.getLogger('sample_reg_csv')
    log.setFile(csvName, overwrite=True)
    log.setFileFormat("simple")
    #fast
    log.setConsoleLevel("ERROR")

    startTime = time.perf_counter()
    count=0
    header = '%10s' % "Time,"
    workload = stress()
    for j in range (40000):
        #time.sleep(0.1)# it will take 0.2s per sample
        now = time.perf_counter()
        samplingtime= now - startTime
        #oneshotpcudata = scan.cpu[0].uncore.pcudata_accesses([(1,0x23bd0)]*65000)
        oneshotpcudata0 = sv.socket0.pcudata.mclos_pid_threshold_limit
        oneshotpcudata1 = sv.socket0.pcudata.mclos_pid_budget
        oneshotpcudata2 = sv.socket0.pcudata.mclos_pid_budget_delta
        oneshotpcudata3 = sv.socket0.pcudata.mclos_drc_rpq_occupancy_max
        sampleLine = '%9.5f,'  % samplingtime
        sampleLine =sampleLine + ("%d," %( oneshotpcudata0))
        sampleLine =sampleLine + ("%d," %( oneshotpcudata1))
        sampleLine =sampleLine + ("%d," %( oneshotpcudata2))
        sampleLine =sampleLine + ("%d," %( oneshotpcudata3))
        if csvName is not None:
            # if count%15 == 0 and not needForCsv: log.result('\n'+header)
            log.result(sampleLine)
        else:
            if count % 15 == 0: 
                print('\n' + header)
            print(sampleLine)
            count += 1
    workload.wait()

def stress():
    cmd = "bash /root/icx_microcode/hwdrc_postsi/scripts/workload.sh S0"
    obj = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    return obj

def set_point(value):
    print("setpoint: %s" % value)
    # os.system("cd /root/icx_microcode/hwdrc_postsi/scripts/ ; /root/icx_microcode/hwdrc_postsi/scripts/hwdrc_change_setpoint.sh %s" % value)
    os.system("cd /root/icx_microcode/hwdrc_postsi/scripts/ ; bash /root/icx_microcode/hwdrc_postsi/scripts/hwdrc_change_setpoint.sh %s" % value )


def run_csv(filename):
    fd = csv.DictReader(open(filename, encoding='utf-8-sig'))
    for row in fd:
        print (row)
        pid_scaling(int(row["kp"]), int(row["ki"]), 0, int(row["setpoint"]))


filename = "/root/icx_microcode/hwdrc_postsi/Kp_Ki_setpoint.csv"
#run_csv(filename)
