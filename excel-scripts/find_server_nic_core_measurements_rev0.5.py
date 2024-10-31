#!/usr/bin/env python
import os
import csv
import sys
import subprocess
import time
import re
import datetime
import optparse
from collections import defaultdict
import statistics as stat
import pandas as pd


if(len(sys.argv) <3):
    print("Usage ./process_.py <datadir> <outfile>  provide abs path")
    exit()

else:
    curdir = sys.argv[1]
    outfilename = sys.argv[2]
    servercore = sys.argv[3]

usecore = ""

if servercore == "all":
    usecore = "4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27"
elif servercore == "subset":
    usecore = "4,5,6,7,8,9,12,13,24,25,26,27"
else:
     usecore = "4,5,6,7,8,9,12,13,24,25,26,27"


filelist = list()

changedir = os.path.join(os.getcwd(),curdir)


os.chdir(changedir)

try:
	os.remove(outfilename)

except OSError:
	pass




nicfiles = ""
servfiles = ""
for file in os.listdir("./"):
	if re.search(r'.*coreview.*', file):
		m = re.search(r'read(.*)pat(.*)_coreview.csv', file)
		name = m.group(1) + "," + m.group(2)
		serverfile = "server_" + m.group(1) + "_" + m.group(2)
		nicfile = "nic_" + m.group(1) + "_" + m.group(2)
		filepath = file
		
		cleancorefile = "/pnpdata/EDPprocess/csv_exp/cleancoreviewfiles.sh " + filepath
		os.system(cleancorefile)

#select the 2xclient server and nic core data

		niccoreselect = "/pnpdata/EDPprocess/csv_exp/select_specific_rows.py -f " + filepath + " -t core -n 0,1,2,3 -o  " + nicfile
		serverselect = "/pnpdata/EDPprocess/csv_exp/select_specific_rows.py -f " + filepath + " -t core -n " + usecore + " -o " + serverfile
		#serverselect = "/pnpdata/EDPprocess/csv_exp/select_specific_rows.py -f " + filepath + " -t core -n 4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27 -o " + serverfile
		os.system(niccoreselect)
		os.system(serverselect)
		processservercore = "/pnpdata/EDPprocess/csv_exp/process_core_threadviewfiles.py -f " + serverfile + ".csv  -m /pnpdata/EDPprocess/csv_exp/metric_list_2lm.txt"
		processniccore = "/pnpdata/EDPprocess/csv_exp/process_core_threadviewfiles.py -f " + nicfile + ".csv  -m /pnpdata/EDPprocess/csv_exp/metric_list_2lm.txt"
		
		os.system( processservercore)
		os.system(processniccore)
		nicfiles = nicfiles + nicfile + "_analysis.csv,"
		servfiles = servfiles + serverfile + "_analysis.csv,"



#select max and average for nic and server cores and write into separate nic and server files


analysecmd = "/pnpdata/EDPprocess/csv_exp/get_metric_of_interest.py -f  " + nicfiles + servfiles.strip(",") + " -t max -c row -m /pnpdata/EDPprocess/csv_exp/core_metric.txt -o " + "max.csv"
os.system(analysecmd)
analysecmd = "/pnpdata/EDPprocess/csv_exp/get_metric_of_interest.py -f  " + nicfiles + servfiles.strip(",") + " -t avg -c row -m /pnpdata/EDPprocess/csv_exp/core_metric.txt -o " + "avg.csv"
os.system(analysecmd)
max = pd.read_csv("max.csv", header=0, skip_blank_lines=True, index_col=0)
avg = pd.read_csv("avg.csv", header=0, skip_blank_lines=True, index_col=0)

df = pd.concat([max, avg], axis=1, join_axes=[max.index])

#df = pd.read_csv(outfilename, header=0, skip_blank_lines=True, index_col=0)

#df.columns = [m.group(1) + "," + m.group(2) + "," + m.group(3) m = re.search(r'(\D+_\D+)_(\d+)_(\D+:\D+)_\D*', col) for col in df.columns]

columns = []

for col in df.columns:
	m = re.search(r'(\D+_\D+)_(\d+)_(\D+:\D+)_\D*', col)
	text = m.group(1) + "," + m.group(2) + "," + m.group(3)
	columns.append(text)

print(columns)


new = df.T

#new.columns = [m.group(1),m.group(2),m.group(3) m = re.search(r'(\D+_\D+)_(\d+)_(\D+:\D+)_\D*', col) for col in new.columns]

#new.columns.values[0] = 'test'
new["case,num,pat"] = columns
new.index.name = 'test'
new.to_csv(outfilename)

os.system("sed -i 's/\"//g' " + outfilename)

#df.columns.values[0] = 'metric'

os.system("rm -f *_analysis*")


#os.system("p")
 
