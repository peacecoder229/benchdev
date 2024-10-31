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

# This porgram parses a single servercore or niccore file and provide avg, max etc over the columns and create an outputfile names _analysis.csv


def get_opts():
	"""
	read user params
	:return: option object
	"""

	parser = optparse.OptionParser()
	parser.add_option("-f", "--filenames", dest="files",
			help="provide the filenames to parse by comma")
	parser.add_option("-m", "--metricfile", dest="metricfile",
			help="provide the file with list of metrics to parse")


	(options, args) = parser.parse_args()

	return options



def run_resultparser(options):

	csvfiles = options.files.split(",")
	print(csvfiles)
	metriclist = [line.strip() for line in open(options.metricfile, "r").readlines()]
	dflist = []

	for file in csvfiles:
			df = pd.read_csv(file, header=0, skip_blank_lines=True, index_col=0)
			df.columns = [col + "_" + file for col in df.columns]
			outfilename = file.replace(".csv", "") + "_analysis.csv"


	rowname = df.index
	#choosing the rownames which matches each tag in the metriclist
	metrictochoose = [entry for tag in metriclist for entry in rowname if tag in entry]
	print( metrictochoose)
	df_sub = df.loc[metrictochoose]
	#df_sub.replace('', np.nan, inplace=True)
	df_sub.to_csv("tmp.csv")
	df_al = df_sub
	df_al['cmax'] = df_sub.idxmax(axis=1)
	#df_al['cmin'] = df_sub.idxmin(axis=1, skipna=True)
	df_al['max'] = df_sub.max(axis=1)
	df_al['min'] = df_sub.min(axis=1)
	df_al['avg'] = df_sub.mean(axis=1)
	df_al['delta'] =  (df_al['max'] - df_al['min'])/df_al['avg']
	df_sorted = df_al.nlargest(2500, 'delta')
	#print(df_sorted.columns)
	#print(df_sorted[['max', 'min', 'avg', 'delta', 'cmax']])		



	df_sorted.to_csv(outfilename)
	




if __name__ == "__main__":

	options = get_opts()
	run_resultparser(options)
