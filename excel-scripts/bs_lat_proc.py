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


file = sys.argv[1]

i=0
vip = list()
se = list()
for line in open(file, 'r').readlines():
	data = line.strip().split()
	n=i%4
	if n == 0:
		se.append(data)
	elif n == 1:
		se.append(data)
	elif n == 2:
		vip.append(data)
	else:
		vip.append(data)
	i = i + 1

for ele in range(len(vip)):
	n = ele % 2
	if n == 0:
		first = vip[ele]
	else :
		second = vip[ele]
	if n == 1:
		print(second[0] + "," + second[1] + "," + second[2] + "," + first[2])
print("SE,start,here")

for ele in range(len(se)):
	n = ele % 2
	if n == 0:
		first = se[ele]
	else :
		second = se[ele]
	if n == 1:
		print(second[0] + "," + second[1] + "," + second[2] + "," + first[2])
