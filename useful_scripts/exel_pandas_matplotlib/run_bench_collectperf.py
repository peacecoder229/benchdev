#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import re
import signal
import pandas as pd
import matplotlib
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_agregate(df, met1, met2, xvar, title):
  print(df.columns)
  pid_met1 = df[met1]
  xval = df[xvar]
  pid_met2 = df[met2]
  fig, ax1 = plt.subplots(figsize=(75,15))
  fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
  ax2 = ax1.twinx()
  ax1.plot(xval, pid_met1, Label = met1, color ='r', marker = 'o')
  ax1.set_xlabel(xvar, fontsize=24)
  plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
  plt.setp(ax1.get_yticklabels(), fontsize=20)
  ax1.set_ylabel(met1, fontsize=28)
  ax1.legend(bbox_to_anchor=(0.25, 0.75), loc='upper left', fontsize=20)
  ax2.plot(xval, pid_met2, Label = met2, color ='b', marker = 'x')
  plt.setp(ax2.get_yticklabels(), fontsize=20)
  ax2.set_ylabel(met2, fontsize=28)
  ax2.legend(bbox_to_anchor=(0.75, 0.75), loc='upper right', fontsize=20)
  plt.tight_layout()
  ax1.grid()
  ax2.grid()
  plt.savefig("%s_%s_%s.pdf" %(title, met1, met2), dpi=300, transparent=True,pad_inches=0)








def checkifanyitemsinline(mylist, lookup):
    for s in lookup:
        n = next((x for x in mylist if x in s),None)
        if n is not None:
            return n


def perflineout(buf):
    for l in iter(buf.readline, ""):
        if not re.findall(r'time', l):
            yield l



def run_and_process(bench, perf, buftype):
    if(buftype == "stderr"):
        perf = subprocess.Popen(perf, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        buf = perf.stderr
    else:
        perf = subprocess.Popen(perf, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        buf = perf.stdout
    bench = subprocess.Popen(bench, stdout=subprocess.PIPE, shell=True)
    #for i in execute_perf(perf.stderr):
    #    print(i)
    getperf = perflineout(buf)
    while bench.poll() is None:
        l = next(getperf)
        l = re.split("\s+", l)
        print(l[1])
    perf.send_signal(signal.SIGINT)
   

def runhplp_perf(bench, benchlp, hpcore, lpcore):
        
    hpperf = "perf stat  -C %s -I 1000 -e tsc,ref-cycles,instructions " %(hpcore) if hpcore else None
    lpperf = "perf stat  -C %s -I 1000 -e tsc,ref-cycles,instructions " %(lpcore) if lpcore else None
    if hpperf:
        hpperf = subprocess.Popen(hpperf, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
         
    if lpperf:
        lpperf = subprocess.Popen(lpperf, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
 
        
    runbench = subprocess.Popen(bench['cmd'], stdout=subprocess.PIPE, shell=True)
    if lpcore:
        runbenchlp = subprocess.Popen(benchlp['cmd'], stdout=subprocess.PIPE, shell=True)
    #for i in execute_perf(perf.stderr):
    #    print(i)
    gethp = perflineout(hpperf.stderr) if hpperf else None
    getlp = perflineout(lpperf.stderr) if lpperf else None
    data = dict()
    data['time'] = list()
    itm = ["tsc", "ref-cycles", "instructions"]
    for i in itm:
        data[i + "_hp"] = list()
        data[i + "_lp"] = list()
        
    while runbench.poll() is None:
        if gethp:
            hpl = next(gethp)
            l = re.split("\s+", hpl)
            data['time'].append(l[1])
            print("last item is  %s\n" %(l[3]))
            data[l[3] + "_hp"].append(l[2].replace(',', ''))
            print("HP " +  l[1])
        if getlp:
            lpl = next(getlp)
            l = re.split("\s+", lpl)
            data[l[3] + "_lp"].append(l[2].replace(',', ''))
            print("LP " +  l[1])
        #else:
        #    print("Nothing")
    hpperf.send_signal(signal.SIGINT)
    if getlp:
        lpperf.send_signal(signal.SIGINT)
    if lpcore:
        runbenchlp.send_signal(signal.SIGINT)

    df = pd.DataFrame.from_dict(data, orient='index').transpose()
    cols = df.columns
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    if lpcore:
        df['lputil'] = df['ref-cycles_lp']/df['tsc_lp']
        df['lpipc'] = df['instructions_lp']/df['ref-cycles_lp']
    else:
        pass
    df['hputil'] = df['ref-cycles_hp']/df['tsc_hp']
    df['hpipc'] = df['instructions_hp']/df['ref-cycles_hp']

    plot_agregate(df, 'hputil', 'hpipc', 'time', bench['title'])
    if lpcore:
        plot_agregate(df, 'lputil', 'lpipc', 'time', benchlp['title'])

    
    
if __name__ == "__main__":
    #bench = sys.argv[1]
    #perf = sys.argv[2]
    #buftype = sys.argv[3]
    #print("Benchmark %s |||| Perf collector %s  ||||  Type of output %s\n" %(bench, perf, buftype))
    #run_and_process(bench, perf, buftype)
    lpcore = "14-27"
    hpcore = "0-13"
    bench = dict()
    benchlp = dict()
    bench['cmd'] = "./mc_sweep.sh 0-13 drc_res 1"
    #bench['cmd'] = "vmstat 1 10"
    #bench['title'] = "Memcacheonly"  
    #runhplp_perf(bench, None, hpcore, None)
    bench['title'] = "MC_hp_SA_lp"
    benchlp['title'] = "SA_lp_MC_hp"
    benchlp['cmd'] = "docker run --rm  --cpuset-cpus=%s --cpuset-mems=0 -e RUNTIME=660 -e MSIZEMB=16384 stressapp:latest" %(lpcore)
    runhplp_perf(bench, benchlp, hpcore, lpcore)
      

    
 
