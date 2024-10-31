#!/usr/bin/env python3
import os
import csv
import sys
import optparse
import subprocess
import time
import pandas as pd
from pathlib import Path
import re
import matplotlib.pyplot as plt
'''
./process_stats_of_file.py  --filepattern="*rd_con5_d512.txt" --indexpattern="GET" --statpos=1  --indexpos=0
Script to process min and max for a number of files and summarize them
ToDO -> printing help if args are messed up
Then currently df.query('val == @maxv')['case']
is returning more then one case. Figure out a way to sumarizethem. Only their numbers are being reported now.
Could some pattern matchng a cool idea for specific things in those index names

'''


def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("--filepattern", dest="filepat",  help="provide filename rgexp", default=None)
    parser.add_option("--indexpattern", dest="idxpat", help="provide item search rgexp", default=None)
    parser.add_option("--statpos", dest="statpos", help="provide column position for the items for statistical data", default=None)
    parser.add_option("--indexpos", dest="idexpos", help="provide column position for the items for caseitmes.. leftmost is 0.", default=None)
    parser.add_option("--outfile", dest="out", help="provide outfile name", default=None)


    (options, args) = parser.parse_args()
    return options


if __name__ == "__main__":
    options = get_opts()

    files = options.filepat
    #items = options.idxpat
    #statpos = int(options.statpos)
    #idexpos = int(options.idexpos)
    sumfile = options.out
    if (files is None):
        print("options not set right. Please check --help")
        sys.exit(1)

    allfiles = list()
    dir = os.getcwd()
    for path in Path(dir).glob(files):
        # rglob provide recursive file discovery
        allfiles.append(path.name)
        print(path.name)
    sum = open(sumfile, "w")
    sum.write("workload,corecount,minlat,maxlat,avglat,minbw,maxbw,avgbw,minrpq,maxrpq,avgrpq\n")
    print("I am executing")

    for f in allfiles:
        m =  m = re.match(r'm(\d+)_.*_mb100_([a-zA-Z]+)_.*txt', f)
        cc = m.group(1)
        wkld = m.group(2)
        name = ["s0bw", "s0lat", "s0rpq", "s1bw", "s1lat", "s1rpq"]
        col = [wkld + "_" + cc + "_" + s for s in name]
        print(col)
        df = pd.read_csv(f,header=None, names = col)
        #All stats calculation

        sockbw = wkld + "_" + cc + "_" +  "s0bw"
        socklat =  wkld + "_" + cc + "_" +  "s0lat"
        sockrpq =  wkld + "_" + cc + "_" +  "s0rpq"

        minl = df[socklat].min()
        maxl = df[socklat].max()
        avgl = df[socklat].mean()
        minbw =  df[sockbw].min()
        maxbw = df[sockbw].max()
        avgbw = df[sockbw].mean()
        minq = df[sockrpq].min()
        maxq = df[sockrpq].max()
        avgq = df[sockrpq].mean()

        sum.write(wkld + "," + cc + "," + str(minl) + "," + str(maxl) + "," + str(avgl) + "," + str(minbw) + "," + str(maxbw) + "," + str(avgbw) + "," + str(minq) + "," + str(maxq) + "," + str(avgq) + "\n")






        plt.plot(df.index, df[sockbw], label = sockbw)
        #plt.plot(df.index, df[socklat], label = socklat)
        plt.ylabel("Scoket BW in MB/S")
        #plt.ylabel("RPQ latency in ns ")
        plt.title(wkld +  "Memory BW")
        plt.legend()
        #print(f + "data" + df[sockbw])

    #plt.savefig(wkld + "_bw.pdf")
    plt.savefig(wkld + "_bw.pdf")








