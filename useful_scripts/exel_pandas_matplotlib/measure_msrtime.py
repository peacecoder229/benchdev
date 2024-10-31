import sys,os
import time


time_start = float(time.time())
i=0
while i < 10000:
	os.system("rdmsr 0x199")
	i=+1

time_end = float(time.time())

avg_time = (time_end - time_start)/10000

print("Avag is " + avg_time)
