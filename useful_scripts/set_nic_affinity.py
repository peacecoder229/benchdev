#!/usr/bin/env python3
import os
import csv
import sys
import subprocess
import time
import re
import datetime
import optparse

sys.stdout = open('logfile.nic_affinity', 'w')

def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("-i", "--intmap", dest="interface",
                      default="eth1:0",
                      help="all the NIC names and desired cores whr intr are to be  mapped to given by seperate by + eth1:0,1+eth2:9,11")

    parser.add_option("-c", "--corecount", dest="totalcore",
                      default="32",
                      help="provide total no of cores in the system with -c option") 

    (options, args) = parser.parse_args()
    if(len(sys.argv) == 1):
      print(parser.print_help())
      exit()
    else:
      return options

def set_nic(options):
    #ifcinfo = options.interface.split(" ")
	#print( options.interface + " " + options.totalcore )
	niclabels = ['ifc', 'corelist']
	nicmapping = [dict(zip(niclabels, ifc.split(":"))) for ifc in options.interface.split("+")]
	i = 0
    # for each ifc and core combo
    # find all RxTx interupt numbers
    # for each RxTx interrupt map it to a core. shd be mapped to len(RxTx)%len(cores). equally divinding all RxTx in a circular manner to
    # available cores
	for i in range(len(nicmapping)):
	#print("IFC name is " + nicmapping[i]['ifc'])
		totalcore = str(int(int(options.totalcore)/4))
		#below formatting to convert a number to hex with totalcore bit
		sfrmat = "\"%0"+totalcore+"X\""
		#first based on core number 1 is shifted to left to create binary representation of teh core position.
		#for example core 8 is the 9 position on the core masksetting and 1 is shifted by 8 to the left
		nicmapping[i]['corelist'] = [1 << int(core) for core in nicmapping[i]['corelist'].split(",")]
		#Binary value if converted into a hex value
		nicmapping[i]['corelist'] = [sfrmat % int(core) for core in nicmapping[i]['corelist']]
      	#find all the TxRx interrupt names and numbers for each interface
		cmd = "cat /proc/interrupts | grep " + nicmapping[i]['ifc'] + ".TxRx"
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(txrxlist, err) = proc.communicate()
		txrxlist = txrxlist.splitlines()
		txrxinfo = list()
		totalcore = len(nicmapping[i]['corelist'])
		curq = 0
		for ele in txrxlist:
			core_to_assign = curq % totalcore
			#print(ele)
			line = ele.decode()
			line = line.strip()
			#print(line)
			ele_list = line.split()
			no = ele_list[0].rstrip(":")
			name = ele_list[-1]
			print("intr name and no " + name + " " + str(no) + " core to assign is " + nicmapping[i]['corelist'][core_to_assign])
			print("current affinity is")
			p = subprocess.Popen("cat /proc/irq/" + str(no) + "/smp_affinity", stdout=subprocess.PIPE, shell=True)
			print(p.stdout.read())
			set_affinity = "echo " + nicmapping[i]['corelist'][core_to_assign] + " > /proc/irq/" + str(no) + "/smp_affinity"
			os.system(set_affinity)
			print("New affinity is")
			p = subprocess.Popen("cat /proc/irq/" + str(no) + "/smp_affinity", stdout=subprocess.PIPE, shell=True)
			print(p.stdout.read())
			curq = curq + 1
	  
		i=i+1
    

if __name__ == "__main__":
    options = get_opts()
    set_nic(options)
