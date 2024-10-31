#!/usr/bin/python
import os
import csv
import sys
import subprocess
import time


def run_redis():
    # get log file path
    #os.system("pkill -9 redis")
    killredis = "ps aux | grep -v \"color=auto\" | grep redis-server | awk '{system(\"kill \"$2)}'"
    os.system(killredis)
    time.sleep(15)
    clearcache = "echo 3 > /proc/sys/vm/drop_caches  &&  swapoff -a  && swapon -a && printf \"\n%s\n\" \"Ram-cache and Swap Cleared\""
    os.system(clearcache)
    nohugepage = "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
    os.system(nohugepage)	
    val = os.system("lscpu | grep \"NUMA node. CPU\" | awk '{print $4}' > numa.txt")
    portlist=(9001,9501)
    n=0
    iplist=('192.168.1.99', '192.168.2.99', '192.168.3.99', '192.168.4.99', '192.168.5.99', '192.168.6.99', '192.168.7.99', '192.168.8.99')
    with open('numa.txt') as nmfile:
	for line in nmfile:
    	  (scmin,scmax) = map(int, line.strip().split("-"))
    	  port = portlist[n]
          k = 0
    	  for i in range(scmin+4,(scmax+1)/2):
		  ip = iplist[k%8]
		  port = port + 1	
        	  rt = str(port)
        	  core = str(i)	
    		  cmd = "taskset -c " + core + " /usr/bin/redis-server  --port " + rt + " --bind " + ip + " &"
                  print(ip + ":" + rt)
		  os.system(cmd)
		  #time.sleep(8)
		  k=k+1

    	  for i in range((scmax+9)/2,scmax+1):
		  ip = iplist[k%8]
		  port = port + 1	
        	  rt = str(port)
        	  core = str(i)	
    		  cmd = "taskset -c " + core + " /usr/bin/redis-server  --port " + rt + " --bind " + ip + " &"
                  print(ip + ":" + rt)
		  os.system(cmd)
		  #time.sleep(8)
		  k=k+1
	  time.sleep(2)
	os.system("rm numa.txt")		
	print("DONE")


if __name__ == "__main__":

        run_redis()
        print("I am quitting")
