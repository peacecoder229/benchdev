#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from multiprocessing import Pool
import os 
import matplotlib.pyplot as plt 
from functools import reduce

register_convertion = lambda a: a & ((0x1<<31) -1)

def read_datafile(name):
    print("begin to processing %s" %name)

    df = pd.read_csv(name, names=["ts","th_limit", "budget", "delta", "rpq_occ"], index_col=False)
    tag = name.replace(".csv", ".png")
    plot_data(df, tag)
    
    p, i, d, sp = tuple(name.replace(".csv", "").split("_"))
    df["p"] = p
    df["i"] = i
    df["d"] = d
    df["sp"] = sp
    
    df.delta = df.delta.apply(register_convertion)
    
    return df


def plot_data(df, filename):
    fig = plt.figure(filename)
    
    for i,v  in enumerate(["th_limit", "budget", "rpq_occ"]):
        ax_copy = fig.add_subplot(2, 2, i+1)
        df[v].plot(ax=ax_copy, fontsize=4,)
        ax_copy.set_title(v)
        
    ax_copy = fig.add_subplot(2, 2, 4)
    ax_copy.set_title("RPQ hist")
    
    plt.savefig(filename, dpi=300, transparent=True,pad_inches=0)

    
def summary_data(df):
    
    return df

def main(path="."):
    filelist = []
    for d in os.listdir(path):
        if not d.endswith("csv"):
            continue
        filelist.append(d)
    
    # map reduce phase

    threads = 128
    if threads > 1:
        p= Pool(threads)
        summary = p.map(read_datafile, filelist)
    else:
        summary = map(read_datafile, filelist)

    final = reduce(lambda a,b : a.append(b, ignore_index=True), summary)
    final.to_csv("all_data_summary.txt")

    # RPQ occ summary
    print("==========%s==========" % "min")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].min()) 
    print("==========%s==========" % "max")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].max()) 
    print("==========%s==========" % "avg")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].mean())
    
    print("==========%s==========" % "p5")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.05))
    print("==========%s==========" % "p50")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.5))
    print("==========%s==========" % "p95")
    print(final.groupby(["p", "i", "d", "sp"])["rpq_occ"].quantile(0.95))

    
if __name__ == "__main__":
    main()
