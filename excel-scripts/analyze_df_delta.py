#!/usr/bin/env python
import os
import csv
import sys
import subprocess
import time
import re
import datetime
import optparse
import pandas as pd
import numpy as np

def get_opts():
	"""
	read user params
	:return: option object
	"""

	parser = optparse.OptionParser()
	parser.add_option("-f", "--filenames", dest="files",
			help="provide the filenames to parse by comma")
	parser.add_option("-t", "--text", dest="text",
			help="provide the text portion of the column name")
	parser.add_option("-n", "--numbers", dest="numbers",
			help="provide numbers seprate by , which comes as suffix")
	parser.add_option("-o", "--outfile", dest="outfile",
			help="provide the name of outputfile")


	(options, args) = parser.parse_args()

	return options



def run_resultparser(options):

	csvfiles = options.files.split(",")
	#print(csvfiles)
	dflist = []
	for file in csvfiles:
            name = file.replace(".csv", "")
	    name = pd.read_csv(file, header=0, skip_blank_lines=True, index_col=0)
            dflist.append(name)
        # print("master is " + dflist[0])
        #print(dflist[0].shape)
        dfmaster = dflist[0].transpose()
        cols = dfmaster.columns
        dfmaster[cols] = dfmaster[cols].apply(pd.to_numeric, errors='coerce')
        flt = (dfmaster['metric_CPU utilization %'] > 5)
        dfmaster = dfmaster[flt]
        mst_avg = list()
        for col in dfmaster.columns:
            Avg = dfmaster[col].mean()
            mst_avg.append(Avg)

        #dfmaster.append({'metaverage':mst_avg}, ignore_index=True)
        #Below is how to add a row to an Dataframe  name with loc and add the list
        dfmaster.loc['Average'] = mst_avg
        #Below for finding if any of the columns is nan
        #df1 = dfmaster[dfmaster.isna().any(axis=1)]
        # Drop all columns with nan values like below
        dfmaster.dropna(axis = 1, how = 'all', inplace=True)
        #print(dfmaster.index)
        #print(df1)

            
       # print(dfmaster.loc['avg'])
	for i in range(1, len(dflist)):
            #print(dflist[i].shape)
            df_t = dflist[i].transpose()
            cols = df_t.columns
            df_t[cols] = df_t[cols].apply(pd.to_numeric, errors='coerce')
            flt = (df_t['metric_CPU utilization %'] > 5)
            df_t = df_t[flt]
            avg = list()
            for col in df_t.columns:
                Avg = df_t[col].mean()
                avg.append(Avg)

            df_t.loc['Average'] = avg
            df_t.dropna(axis = 1, how = 'all', inplace=True)
            s = (df_t.loc['Average']/dfmaster.loc['Average'])
            #shows filtering with series
            #taking ratio of averages across the cpus ( rows) and finding out which average values  ones is 3x times more
            s = s[s > 3]
            #filetring with loc does not work.. 
            #df_t.loc['diff'] = s.tolist() 
            #flt = (df_t.loc['diff'] > 10)
            #print(flt)
            #find = df_t.loc[flt]
            print(dfmaster.shape)
            print(df_t.shape)
            print(s)

#create mtaplotlib files




if __name__ == "__main__":

	options = get_opts()
	run_resultparser(options)
