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
from pathlib import Path

def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("--outputfile", dest="outfile", help="provide Output file name", default=None)
    parser.add_option("--variablepos", dest="varpos", help="provide positions of variables when column name is split with varpattern like a dict {0:delay, 2:cores} etc", default=None)
    parser.add_option("--variablesep", dest="varsep", help="provide separator charecter that can be used to extract variable names sucg as - or , ", default=None)
    parser.add_option("--stattype", dest="metric", help="provide min  max or mean etc stats operation desried on the columns", default="mean()")
    parser.add_option("--filepattern", dest="filepat",  help="provide filename rgexp", default=None)
    parser.add_option("--columns", dest="items", help="provide all csv columns that needs to be processed like hplat,hpbw,lpbw etc", default=None)
    (options, args) = parser.parse_args()
    return options



if __name__ == "__main__":
    options = get_opts()
    csvpat = options.filepat
    outfile = options.outfile
    items = re.split(r",", options.items)
    data = dict()
# for json.loads to works  variable need to be inside single quote --variablepos='{"2" : "delay", "1" : "cores"}'
    vardict = json.loads(options.varpos)
    varsep = options.varsep
    stat = options.metric
    print("Stattype is %s\n" %(stat))
    if(outfile is None or vardict is None or varsep is None or options.items is None):
        print("options not set right. Please check --help")
        sys.exit(1)
    
    for itm in items:
        data[itm] = list()

    for k,v in vardict.items():
        data[v] = list()
    dir = os.getcwd()
    for path in Path(dir).glob(csvpat):
        csv = path.name
        df = pd.read_csv(csv, sep=",", header=0)
        c = df.columns
        df[c] = df[c].apply(pd.to_numeric, errors='coerce') 
        dfmlc = df.iloc[0:1]
        for itm in items:
            #print(df[itm])
            if not re.search(r'rpq', itm):
                print(itm)
                data[itm].append(dfmlc[itm].mean())
            else:
                data[itm].append(df[itm].mean())
            
        #val = re.split(r"%s" %(varsep), c)
        csv = csv.replace(".csv", "")
        val = re.split(r"_", csv)
        for k,v in vardict.items():
            k = int(k)
            data[v].append(val[k])

    result_df = pd.DataFrame.from_dict(data, orient='index').transpose()



    result_df.to_csv(outfile, sep = ",", index=False)



