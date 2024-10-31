#!/usr/bin/env python3
# coding: utf-8


import pandas as pd
from multiprocessing import Pool
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re
import sys
from functools import reduce
out = open("Average_stat.txt", "w")
line = ""
for itm in ["pid_out", "budget", "ewma_delta", "rpq_occ"]:
    line = line + itm + "_p10," + itm + "_avg," + itm + "_p75,"
out.write(line + "p,i,d,sp,ewma")
out.write("\n")

register_convertion = lambda a: a & ((0x1<<31) -1)

def correctreg32(x):
    if x > (2**31 -1):
        return (x - 2**32)
    else:
        return x

def read_datafile(path, name, out, figlist, color):
    print("begin to processing %s" %name)
    fname = os.path.join(path, name)

    df = pd.read_csv(fname, names=["ts","pid_out", "budget", "ewma_delta", "rpq_occ"], index_col=False)
    #df = df.iloc[8000:14000]
    c = df.columns
    df[c] = df[c].apply(pd.to_numeric, errors='coerce')
    df["budget"] = df["budget"].apply(lambda x: correctreg32(x))
    df["ewma_delta"] = df["ewma_delta"].apply(lambda x: correctreg32(x))

    runname = name.replace(".csv", "")
    ewma_val = runname.split("_")[4]
    setp = runname.split("_")[3]
    tag = "%s_%s" %(setp,ewma_val)
    #plot_data(df, tag)
    #plot_ewma(df, tag)
    for met in ["pid_out", "budget", "ewma_delta", "rpq_occ"]:
        plot_met(df, met, tag, figlist[met], color)

    p, i, d, sp, ema = tuple(name.replace(".csv", "").split("_"))
    df["p"] = p
    df["i"] = i
    df["d"] = d
    df["sp"] = sp
    df["ewma"] = ema
    tag = "%s_%s" %(sp,ema)
    print("Tag is %s\n" %(tag))
    
    #df.ewma_delta = df.ewma_delta.apply(register_convertion)

    line = ""
    for itm in ["pid_out", "budget", "ewma_delta", "rpq_occ"]:
        #p10 = df[itm].quantile(0.1)
        #avg = df[itm].mean()
        #p75 = df[itm].quantile(0.75)
        p10 = df[itm].min()
        avg = df[itm].mean()
        p75 = df[itm].max()
        line = line + "%s,%s,%s," %(p10, avg, p75) 

    #out = open("Average_stat.txt", "a")
    out.write(line + p + "," + i + "," + d + "," + sp + "," + ema)
    out.write("\n")
    print(line)
    print("\n")
    #out.close()
    
    return df


def plot_data(df, filename):
    fig = plt.figure(filename)
    
    for i,v  in enumerate(["budget", "rpq_occ", "pid_out"]):
        ax_copy = fig.add_subplot(2, 2, i+1)
        df[v].plot(ax=ax_copy, fontsize=4,)
        ax_copy.set_title(v)
        
    ax_copy = fig.add_subplot(2, 2, 4)
    ax_copy.hist(df["rpq_occ"])
    ax_copy.set_title("RPQ hist")
    p, i, d, sp, ema = tuple(filename.replace(".png", "").split("_"))
    text = "kp=%s Ki=%s Kd=%s sp=%s ewma=%s" %(p,i,d,sp,ema)
    plt.figtext(0.35, 0.95, text) 
    plt.savefig(filename, dpi=300, transparent=True,pad_inches=0)

    
def plot_met(df, met, tag, ax_copy, color):
    #fig = plt.figure(filename)
    #fig = plt.figure()
    
    #for i,v  in enumerate(["budget", "rpq_occ", "pid_out", "ewma_delta"]):
    #ax_copy = fig.add_subplot(2, 2, i+1)
    df[met].plot(ax=ax_copy, label=tag, fontsize=4, color=color, legend=True)
    #ax_copy.legend(tag)
    ax_copy.set_title(met)
        
def plot_ewma(df, filename):
    #fig = plt.figure(filename)
    fig = plt.figure()
    
    for i,v  in enumerate(["budget", "rpq_occ", "pid_out", "ewma_delta"]):
        ax_copy = fig.add_subplot(2, 2, i+1)
        df[v].plot(ax=ax_copy, fontsize=4,)
        ax_copy.set_title(v)
        
    p, i, d, sp, ema = tuple(filename.replace(".png", "").split("_"))
    text = "kp=%s Ki=%s Kd=%s sp=%s ewma=%s" %(p,i,d,sp,ema)
    plt.figtext(0.35, 0.95, text) 
    plt.savefig(filename, dpi=300, transparent=True,pad_inches=0)
def summary_data(df):
    
    return df

def main(path, pattern):
    pat = re.compile(pattern)
    filelist = []
    for d in os.listdir(path):
        if not d.endswith("csv"):
            continue
        else:
            if re.search(pat, d):
                filelist.append(d)
    figlist = dict()
    for met in ["pid_out", "budget", "ewma_delta", "rpq_occ"]:
        figname = "fig_%s" %(met)
        figname = plt.figure()
        figlist[met] = figname.add_subplot(1,1,1)
    colortop = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    #colortop = ['Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd']
    i=0
    for f in filelist:
        i = i %7
        read_datafile(path, f, out, figlist, colortop[i])
        i += 1

    out.close()
    for met in ["pid_out", "budget", "ewma_delta", "rpq_occ"]:
        pdfname = "%s/%s.pdf" %(path,met)
        figlist[met].figure.savefig(pdfname, dpi=300, transparent=True,pad_inches=0)

    
    # map reduce phase

    #threads = 128
    #if threads > 1:
    #    p= Pool(threads)
    #    summary = p.map(read_datafile, filelist)
    #else:
    #    summary = map(read_datafile, filelist)

    #final = reduce(lambda a,b : a.append(b, ignore_index=True), summary)
    #final.to_csv("all_data_summary.txt")

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
    path = sys.argv[1]
    pat = sys.argv[2]
    main(path,pat)
