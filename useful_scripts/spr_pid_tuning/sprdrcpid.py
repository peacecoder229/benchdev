
sv.refresh()
#import pm.pmdebug as d
#d.general.load_pcode_debug_vars(r"/home/pid_tuning/20210316_8d710210_21ww04f_timewindow_distribution_fix_sync_with_latest_change_x32_remove_fuse_v2/pcode.dbg.gz")

import time
import sys
import csv
import os
import subprocess
import svtools.logging.toolbox as tool
import re

#sumfile = os.path.join(path, "perfsummary.txt")
#global outfile
#outfile = open(sumfile, "a")
#path = "/home/pid_tuning/"
def pid_scaling(p, i, d, sp, ewma):
    #ewma=6
    setp_ewma(sp, ewma)
    sv.socket0.pcudata.mclos_pid_struct_kp = p
    sv.socket0.pcudata.mclos_pid_struct_ki = i
    sv.socket0.pcudata.mclos_pid_struct_kd = d
    # sv.socket0.pcudata.mclos_pid_struct_kd = d
    #set_point(sp)
    # os.exec(./hwdrc_change_setpoint.sh 80)
    global path
    sumfile = os.path.join(path, "perfsummary.txt")
    global outfile
    outfile = open(sumfile, "a")

    csvName="%s_%s_%s_%s_%s.csv" % (p,i,d,sp,ewma)
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
    workload2 = stress_nginx()
    header = "sampleTime,pid_out,pid_budget,ewma_out,rpqocc"
    log.result(header)
    #changed datapoint collections to 80000 from 40000 as nginx running for 30s
    for j in range (80000):
        #time.sleep(0.1)# it will take 0.2s per sample
        now = time.perf_counter()
        samplingtime= now - startTime
        #oneshotpcudata = scan.cpu[0].uncore.pcudata_accesses([(1,0x23bd0)]*65000)
        #pid output
        oneshotpcudata0 = sv.socket0.pcudata.mclos_pid_threshold_limit
        #pid budget created from EWMA filter budget
        oneshotpcudata1 = sv.socket0.pcudata.mclos_pid_budget
        #oneshotpcudata2 = sv.socket0.pcudata.mclos_pid_budget_delta
        #EWMA delta used to generate PID budget
        oneshotpcudata2 = sv.socket0.pcudata.mclos_ewma_budget_delta
        #RPQ OCC input to EWMA filter
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
    for l in workload.stdout.readlines():
        if re.search("numactl --membind", l):
            print("WorkLoad data %s\n" %(l))
            outfile.write("P=%s,I=%s,D=%s,SetP=%s,ewma=%s,res=%s" %(p,i,d,sp,ewma,l))
    for l in workload2.stdout.readlines():
        if re.search("numactl --membind", l):
            print("WorkLoad data %s\n" %(l))
            outfile.write("P=%s,I=%s,D=%s,SetP=%s,ewma=%s,ress=%s" %(p,i,d,sp,ewma,l))
    #workload.wait()
    workload2.wait()
    outfile.close()

def stress():
    #cmd = "bash /home/pid_tuning/scripts/workload.sh S0"
    cmd = "bash /home/pid_tuning/scripts/nginx_only.sh S0"
    #cmd = "bash /home/pid_tuning/scripts/workload_nginx.sh S0"
    obj = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)

    return obj

def stress_nginx():
    #cmd = "bash /home/pid_tuning/scripts/workload.sh S0"
    cmd = "bash /home/pid_tuning/scripts/nginx_2nd.sh S0"
    #cmd = "bash /home/pid_tuning/scripts/workload_nginx.sh S0"
    obj = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True)

    return obj
def set_point(value):
    print("setpoint: %s" % value)
    # os.system("cd /home/pid_tuning/hwdrc_postsi/scripts/ ; /home/pid_tuning/hwdrc_postsi/scripts/hwdrc_change_setpoint.sh %s" % value)
    os.system("cd /home/pid_tuning/scripts/ ; bash /home/pid_tuning/scripts/hwdrc_change_setpoint.sh %s" % value )

def setp_ewma(setp, ewma):
    print("setpoint: %s and EWMA is %s\n" %(setp, ewma))
    # os.system("cd /home/pid_tuning/hwdrc_postsi/scripts/ ; /home/pid_tuning/hwdrc_postsi/scripts/hwdrc_change_setpoint.sh %s" % value)
    os.system("cd /home/pid_tuning/scripts/ ; bash /home/pid_tuning/scripts/hwdrc_change_setpoint.sh %s %s" %(setp, ewma) )

def run_csv(filename):
    fd = csv.DictReader(open(filename, encoding='utf-8-sig'))
    for row in fd:
        print (row)
        pid_scaling(int(row["kp"]), int(row["ki"]), 0, int(row["setpoint"]), int(row["ewma"]))


#filename = "/home/pid_tuning/Kp_Ki_setpoint.csv"
#filename = "/home/pid_tuning/Kp_Ki_setpoint_highsp.csv"
#run_csv(filename)
path = filename.replace(".csv", "")
os.system("mkdir -p " + path)
