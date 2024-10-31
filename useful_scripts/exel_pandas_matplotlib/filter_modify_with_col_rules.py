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
import time

def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("--inputfile", dest="infile", help="provide Input file name", default=None)
    parser.add_option("--outputfile", dest="outfile", help="provide Output file name", default=None)
    parser.add_option("--rule", dest="rule", help="provide string with rule on  cols of CSV like \"'hpcores' : == 16,&,'hpdelay' : == 0,&,'lpcores' : == 16\"", default=None)
    parser.add_option("--sortby", dest="sortkeys", help="provide sortby column names and also True or False for ascending; --sortby='{col1:True, col2:False}'", default=None)
    parser.add_option("--newcol", dest="colrule", help="provide string with colnames and  operation --newcol=\"'cores'=df.hpcores + df.lpcores\" ", default=None)
    (options, args) = parser.parse_args()
    return options



if __name__ == "__main__":
    options = get_opts()
    csv = options.infile
    outfile = options.outfile
    rules = options.rule.split(",") if options.rule else None
    if options.colrule:
        colop = options.colrule.split("=")
        print(colop[0] + "-----------" + colop[1])
    else:
        colop = None
    if options.sortkeys:
        sortkeys = json.loads(options.sortkeys)
    else:
        sortkeys = None



    if(csv is None or outfile is None):
        print("options not set right. Please check --help")
        sys.exit(1)

    df = pd.read_csv(csv, sep=",", header=0)
    c = df.columns
    df[c] = df[c].apply(pd.to_numeric, errors='coerce')
    #add any column based on columns rule
    if colop:
        df[colop[0]]= pd.eval(colop[1])
        #df['cores'] = df['hpcores'] + df['lpcores']

    time.sleep(1)
    #extract rules into synatx applicable for the df
    if rules:
        flt = ""
        for i in rules:
            if i == '&' or i == '|':
                flt = " %s %s " %(flt,i)
            else:
                tmp = i.split(":")
                rulestring = " (df[%s] %s) " %(tmp[0], tmp[1])
                flt = " %s %s " %(flt, rulestring)
        print("filter is %s\n" %(flt))
        df = df[eval("%s" %(flt))]
    else:
        pass
      
    if colop:
        df[colop[0]]= pd.eval(colop[1])
        #df['cores'] = df['hpcores'] + df['lpcores']
    else:
        pass
    sortcol = list()
    ascending = list()
    if sortkeys:
        for k,v in  sortkeys.items():
            print("key is %s and as value is %s\n" %(k, v))
            sortcol.append(k)
            ascending.append(v)
        df.sort_values(sortcol, ascending=ascending, inplace = True)
    else:
        pass 
        
         

    df.to_csv(outfile, sep = ",", index=False)



