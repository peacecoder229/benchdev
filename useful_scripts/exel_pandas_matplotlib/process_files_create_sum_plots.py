#!/usr/bin/env python3
# coding: utf-8


import pandas as pd
from multiprocessing import Pool
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
from functools import reduce

register_convertion = lambda a: a & ((0x1<<31) -1)

def correctreg32(x):
    if x > (2**31 -1):
        return abs(x - 2**32)
    else:
        return abs(x)

def read_datafile(name, outfile):
    print("begin to processing %s" %name)

    df = pd.read_csv(name, names=["ts","th_limit", "budget", "delta", "rpq_occ"], index_col=False)
    c = df.columns
    df[c] = df[c].apply(pd.to_numeric, errors='coerce')
    df["budget"] = df["budget"].apply(lambda x: correctreg32(x))
    df["delta"] = df["delta"].apply(lambda x: correctreg32(x))

    tag = name.replace(".csv", ".png")
    plot_data(df, tag)
    
    p, i, d, sp = tuple(name.replace(".csv", "").split("_"))
    df["p"] = p
    df["i"] = i
    df["d"] = d
    df["sp"] = sp
    
    #df.delta = df.delta.apply(register_convertion)
    df = df.iloc[8500:14500]
    line = "%s," %(name)
    for itm in ["th_limit", "budget", "delta", "rpq_occ"]:
        p10 = df[itm].quantile(0.1)
        avg = df[itm].mean()
        p75 = df[itm].quantile(0.75)
        p99 =  df[itm].quantile(0.99)
        os = p99 - avg
        line = line + "%s,%s,%s,%s," %(p10, avg, p75, os) 

    #out = open("Average_stat.txt", "a")
    out = outfile
    out.write(line + p + ":" + i + ":" + d + ":" + sp + "," + sp + "," + p + i + d + ",")
    out.write("\n")
    print(line)
    print("\n")
    #out.close()
    
    return df


def plot_data(df, filename):
    fig = plt.figure(filename)
    
    for i,v  in enumerate(["budget", "rpq_occ", "th_limit"]):
        ax_copy = fig.add_subplot(2, 2, i+1)
        df[v].plot(ax=ax_copy, fontsize=4,)
        ax_copy.set_title(v)
        
    ax_copy = fig.add_subplot(2, 2, 4)
    ax_copy.hist(df["rpq_occ"])
    ax_copy.set_title("RPQ hist")
    p, i, d, sp = tuple(filename.replace(".png", "").split("_"))
    text = "kp=%s Ki=%s Kd=%s sp=%s" %(p,i,d,sp)
    plt.figtext(0.35, 0.95, text) 
    plt.savefig(filename, dpi=300, transparent=True,pad_inches=0)

    
def summary_data(df):
    
    return df

def plot_pid(files):
  for k in range(0, len(files), 14):
    grp=files[k:k + 14]
    fig = plt.figure("PID_output%s.png" %(k), figsize=(30,15))
    ax_copy = fig.add_subplot(1, 1, 1)
    ii=0
    for name in grp:
       #print("begin to processing %s" %name)

       df = pd.read_csv(name, names=["ts","th_limit", "budget", "delta", "rpq_occ"], index_col=False)
       c = df.columns
       p, i, d, sp = tuple(name.replace(".csv", "").split("_"))
       text="p=%s i=%s sp=%s" %(p,i,sp)
       df[c] = df[c].apply(pd.to_numeric, errors='coerce')
       df["budget"] = df["budget"].apply(lambda x: correctreg32(x))
       df["delta"] = df["delta"].apply(lambda x: correctreg32(x))
       ls=['-','--','-.',':'][ii%4]
       df["th_limit"].plot(ax=ax_copy, fontsize=2, label=text, linestyle=ls,)
       ii += 1
   
    #plt.legend(loc="upper right")
    ax_copy.set_ylabel("PID_O/P", fontsize=20)
    ax_copy.set_xlabel("Timesteps", fontsize=20)
    plt.setp(ax_copy.get_xticklabels(), fontsize=12, rotation=90)
    plt.setp(ax_copy.get_yticklabels(), fontsize=12)
    plt.legend(bbox_to_anchor=(0.7, 0.4), loc='upper right')
    plt.tight_layout()
    plt.savefig("PID_output%s.png" %(k), dpi=300, transparent=True,pad_inches=0)


def plot_agregate(sum_file):
  #df = pd.read_csv(summary, header=0, index_col=False)
  df = pd.read_csv("Average_stat.txt", header=0, index_col=False)
  print(df.columns)
  df_sorted = df.sort_values(by=['p:i:d:sp'], inplace=True, ascending=True)
  pid_os = df_sorted['th_limit_os']
  xval = df_sorted['p:i:d:sp']
  pid_avg = df_sorted['th_limit_avg']
  fig, ax1 = plt.subplots()
  ax2 = ax1.twinx()
  ax1.plot(xval, pid_os, Label = 'overshoot', color ='r')
  ax1.set_xlabel("Kp:Ki:Kd:SetPoint")
  ax1.set_ylabel("Overshoot")
  ax1.legend(bbox_to_anchor=(0.25, 0.75), loc='upper left')
  ax2.plot(xval, pid_avg, Label = 'average', color ='b')
  ax2.set_ylabel("Average")
  ax2.legend(bbox_to_anchor=(0.75, 0.75), loc='upper right')
  plt.tight_layout()
  plt.savefig("Summary_OS_avg.png", dpi=300, transparent=True,pad_inches=0)



def main(path="."):
    
    out = open("Average_stat.txt", "w")
    line = "filename,"
    for itm in ["th_limit", "budget", "delta", "rpq_occ"]:
      line = line + itm + "_p10," + itm + "_avg," + itm + "_p75," + itm + "_os,"
    out.write(line + "p:i:d:sp,sp,pid,")
    out.write("\n")
    filelist = []
    for d in os.listdir(path):
        if not d.endswith("csv"):
            continue
        filelist.append(d)
    
    # map reduce phase
    for f in filelist:
        read_datafile(f, out)
    plot_pid(filelist)
    out.close()
    #threads = 128
    #if threads > 1:
    #    p= Pool(threads)
    #    summary = p.map(read_datafile, filelist)
    #else:
    #    summary = map(read_datafile, filelist)

    #final = reduce(lambda a,b : a.append(b, ignore_index=True), summary)
    #final.to_csv("all_data_summary.txt")
    #plot_agregate("Average_stat.txt")

    # RPQ occ summary
#    print("==========%s==========" % "min")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].min()) 
#    print("==========%s==========" % "max")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].max()) 
#    print("==========%s==========" % "avg")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].mean())
#    
#    print("==========%s==========" % "p5")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.05))
#    print("==========%s==========" % "p50")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.5))
#    print("==========%s==========" % "p95")
#    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.95))

    
if __name__ == "__main__":
    main()
