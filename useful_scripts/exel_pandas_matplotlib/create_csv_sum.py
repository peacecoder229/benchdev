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
import optparse
import json

def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("--inputfile", dest="infile", help="provide Input file name", default=None)
    parser.add_option("--outputfile", dest="outfile", help="provide Output file name", default=None)
    parser.add_option("--variablepos", dest="varpos", help="provide positions of variables when column name is split with varpattern like a dict {0:delay, 2:cores} etc", default=None)
    parser.add_option("--variablesep", dest="varsep", help="provide separator charecter that can be used to extract variable names sucg as - or , ", default=None)
    parser.add_option("--stattype", dest="metric", help="provide min  max or mean etc stats operation desried on the columns", default="mean()")
    (options, args) = parser.parse_args()
    return options



if __name__ == "__main__":
    options = get_opts()
    csv = options.infile
    outfile = options.outfile
    vardict = json.loads(options.varpos)
    varsep = options.varsep
    stat = options.metric
    print("Stattype is %s\n" %(stat))
    if(csv is None or outfile is None or vardict is None or varsep is None):
        print("options not set right. Please check --help")
        sys.exit(1)
    data = dict()
    data[stat] = list()
    for k,v in vardict.items():
        data[v] = list()

    df = pd.read_csv(csv, sep=",", header=0)
    df = df[10:50]
    c = df.columns
    df[c] = df[c].apply(pd.to_numeric, errors='coerce')
    for itm in c:
        print(c)
        #val = re.split(r"%s" %(varsep), c)
        val = re.split(r"_", itm)
        for k,v in vardict.items():
            k = int(k)
            data[v].append(val[k])
        statval = df[itm].mean()
        data[stat].append(statval)   

    result_df = pd.DataFrame.from_dict(data, orient='index').transpose()



    result_df.to_csv(outfile, sep = ",", index=False)



