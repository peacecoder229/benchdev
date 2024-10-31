#!/usr/bin/env python3

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
# os.system("alias python=python3.5")
#import pandas as pd



dirname = sys.argv[1]
outdir = sys.argv[2]
pat = sys.argv[3]
changename = sys.argv[4]
os.system("mkdir -p " + outdir)

for path, subdirs, files in os.walk(dirname):
        #print(path)
	for name in files:
		#print(name)
		if re.search(r"'"+pat+"'", name):
			print("Match" + name)
			file = os.path.join(path, name)
			namelist = os.path.join(path, name).split('/')
			#pattern = pat + r"(.*.csv)"
			#pattern = pat + r"(.*.txt)"
			#m = re.search(pat, namelist[-1])
			#emonfiletype = m.group(1)
			#print(emonfiletype)
			#name = namelist[1] + "_" + namelist[2] + emonfiletype
			if changename:
				print("cp " + file + " to " + name)
				#os.system("mkdir nginx-emon")
				os.system("cp " + file + " " + outdir + "/" + name)
			else:
				os.system("cp " + file + " " + outdir + "/")
