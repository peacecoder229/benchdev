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
	print(csvfiles)
	dflist = []
	numbers = options.numbers.split(",")
	clist = []
	if numbers:
		for n in numbers:
			clist.append(options.text + n)
	print(clist)			
	for file in csvfiles:
			df = pd.read_csv(file, header=0, skip_blank_lines=True, index_col=0)
			df = df[clist]
			#print(df)
			dflist.append(df)
	for df in dflist:
		name = options.outfile + ".csv"
		df.to_csv(name)
	




if __name__ == "__main__":

	options = get_opts()
	run_resultparser(options)
