#!/usr/bin/env python3
import os
import csv
import sys
import optparse
import subprocess
import time
import pandas as pd
from pathlib import Path

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
    usage ./process_stats_of_file.py  --filepattern="inst[0-1]${core}_con${connections}_d512.txt" --indexpattern="GET" --statpos=1 --indexpos=0 --outfile=testsum
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
    items = options.idxpat
    statpos = int(options.statpos)
    idexpos = int(options.idexpos)
    sumfile = options.out
    if (files is None or items is None or statpos is None or idexpos is None):
        print("options not set right. Please check --help")
        sys.exit(1)

    allfiles = list()
    dir = os.getcwd()
    for path in Path(dir).glob(files):
        # rglob provide recursive file discovery
        allfiles.append(path.name)
    sum = open(sumfile, "w") if sumfile else sys.stdout
    sum.write("filename,min,minindex,max,maxindex,avg\n")

    for f in allfiles:
        with open(f, "r") as out:
            data = dict()
            for line in out:
                if line.find(items) > -1:
                    val = line.split()[statpos]
                    index = line.split()[idexpos]
                    data[index] = val
        df = pd.DataFrame(list(data.items()), columns=['case', 'val'])
        df[['val']] =  df[['val']].apply(pd.to_numeric)
        minv = df['val'].min()
        mincase = df.query('val == @minv')['case'].to_list()
        maxv = df['val'].max()
        maxcase = df.query('val == @maxv')['case'].to_list()
        avg = df['val'].mean()
        sum.write(f + "," + str(minv)  + "," + str(len(mincase)) + "," + str(maxv) + "," + str(len(maxcase)) + "," + str(avg) + "\n")








