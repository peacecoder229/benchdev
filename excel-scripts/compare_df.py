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
            tag = name
            name = pd.read_csv(file, header=0, skip_blank_lines=True, index_col=0)
            name.columns = [col + "_" + tag for col in name.columns]
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
        dfmaster.loc['Average'] = mst_avg
        #Below for finding if any of the columns is nan
        #df1 = dfmaster[dfmaster.isna().any(axis=1)]
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
            #shows filtering with series basically find all indexes which is True for below then those indexes are used to find corresponding columns in DF which are True
            #Series index are same as he column names.. series is basically a row.
            s = s[(s > 2) | (s < 0.5)]
            print(dfmaster.shape)
            print(df_t.shape)
            #print(s)
            df_t_loc = df_t[s.index]
            #print(df_t_loc.index)
            #df_t_loc.set_index('metric', inplace=True)
            print( df_t_loc.transpose().shape)
            #print(df_t_loc)
            #df_t_flt = (df_t[s.index]).set_index('metric', inplace=True)
            dfmaster_flt_loc = dfmaster[s.index]
            print(dfmaster_flt_loc.transpose().shape)
        combined = pd.concat( ( df_t_loc.transpose(), dfmaster_flt_loc.transpose()), axis=0, sort=True)  # axis =1 is column wise, noticed with axis=0 and sort=True results in same
        #print(combined)
        combined.to_csv("Combied_2004_1904.csv")



if __name__ == "__main__":

	options = get_opts()
	run_resultparser(options)
