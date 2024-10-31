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

	parser.add_option("-t", "--type", dest="type",
			help="provide type of measurement such as max, min or any names from the columns")

	parser.add_option("-c", "--column", dest="headeroption",
			help="provide -c as row  that can be used for column names or default")

	parser.add_option("-o", "--outfile", dest="outfile",
                        help="provide the name of outputfile")

	(options, args) = parser.parse_args()

	return options



def run_resultparser(options):
	try:
		os.remove(options.outfile)
	except OSError:
		pass

	f = open(options.outfile, "a")
	csvfiles = options.files.split(",")
	print(csvfiles)
	metriclist = [line.strip() for line in open(options.metricfile, "r").readlines()]
	dflist = []
	colnames = ['metric', 'avg_', 'min_', 'max_', '95th_', 'stdd_']

	for file in csvfiles:
		if(options.headeroption == "row"):
			df = pd.read_csv(file, header=0, skip_blank_lines=True, index_col=0)
			df.columns = [col + "_" + file for col in df.columns]
			#print(df)
		else:
			df = pd.read_csv(file, header=None, skiprows=1, names=colnames, index_col=0)
			df.columns = [col + file for col in df.columns]


		rowname = df.index
		#choosing the rownames which matches each tag in the metriclist
		metrictochoose = [entry for tag in metriclist for entry in rowname if tag in entry]
		#print("List of metric to choose\n")
		#print(*metrictochoose, sep="'")
		type = options.type + "_" + file
		df_sub = df.loc[metrictochoose]
		df_type = df_sub[type]
		#df_type.columns = [col + "_" + file for col in df_type.columns]
		#print(df_type)
		dflist.append(df_type)



	fulllist = pd.concat(dflist, axis=1, join_axes=[dflist[0].index])
	delta = type + "_diff"
	#fulllist[delta] = full
	print(fulllist.columns)
	print(fulllist)
	#fulllist[delta] = fulllist.var(axis=1)
	#newlist = fulllist.T
	#newlist = newlist.add_suffix("_" + options.type)
	fulllist.to_csv(f)
	




if __name__ == "__main__":

	options = get_opts()
	run_resultparser(options)
