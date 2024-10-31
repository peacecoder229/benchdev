#!/usr/bin/python
import os
import csv
import sys
import subprocess
import time


def run_redis():
    val = os.system("lscpu | grep \"NUMA node. CPU\" | awk '{print $4}' > numa.txt")
    portlist=(9001,9501)
    n=0
    with open('numa.txt') as nmfile:
	for line in nmfile:
    	  (scmin,scmax) = map(int, line.strip().split("-"))
    	  port = portlist[n]
    	  for i in range(scmin+2,scmax-25):
		  port = port + 1	
        	  rt = str(port)
        	  core = str(i)	
    		  cmd = "/usr/bin/redis-cli -p " + rt + " -h 192.168.0.99 flushall "
		  os.system(cmd)
		  #time.sleep(5)


if __name__ == "__main__":

        run_redis()
