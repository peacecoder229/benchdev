#!/usr/bin/env python
import re
import os
import subprocess
import sys
import pandas as pd


if(len(sys.argv) < 3):
	print("Usage ./process_.py <highlightfile> <exceldatafile>")
	exit()
else:

	HIGHLIGHT_FILE = sys.argv[1]
	DATAFILE = sys.argv[2]

outfilename = DATAFILE + "_selected.csv"
outfile = os.path.join(os.getcwd(),outfilename)

def pick_highlight(highlight, file):
	df = pd.read_excel(DATAFILE, index_col=0, sheetname="raw")
	metric_list = [line.strip() for line in open(highlight, "r").readlines()]
	selected = df.loc[metric_list]
	return selected.T

if __name__ == "__main__":
	output = pick_highlight(HIGHLIGHT_FILE, DATAFILE)
	output.to_csv(outfile)



