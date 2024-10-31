#!/usr/bin/env python3
import os
import csv
import sys
import optparse
import subprocess
import time
import pandas as pd

def get_opts():
    """
    read user params
    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("--basebufsize", dest="basebuf",
                      help="Enter base buffser size in KB.. Multiple of that will be used for different runs", default="1024")
    parser.add_option("--cores", dest="core",
                      help="Enter cores in the format from-to or from-to,from-to", default=None)

    parser.add_option("--runno", dest="maxrun",
                      help="Enter no of runs. Max bufsize =runno*busize ", default="1")

    parser.add_option("--cmd", dest="cmd",
                      help="Ennter the basic benchmark cmdline", default=None)
    parser.add_option("-i", dest="iter",
                      help="Enter no of iterations for each run", default="100")
    parser.add_option("-s", dest="ser",
                      help="Enter if random or seriel access", default=None)
    parser.add_option("--latbwsweep", dest="sweep",
                      help="Enter Yes if want core sweep from 1 to all cores to get lat and BW", default=None)

    parser.add_option("--maxcore", dest="maxcore",
                      help="Eneter maximum number of cores for the run. Min is 0", default="8")
    parser.add_option("--corestep", dest="corestep",
                      help="Enter steps by which cores will be incremented for each run", default="4")

    (options, args) = parser.parse_args()
    return options





if __name__ == "__main__":
    options = get_opts()
    if(options.sweep):
        sweep = True;

    else:
        sweep = False;


    step = int(options.corestep)
    maxcorenum = int(options.maxcore)
    bufsize = int(options.basebuf)
    bufmultiple = int(options.maxrun)
    core = options.core if options.core else "0-" + str(maxcorenum)
    corelist = list()
    print("maxcore= " + str(maxcorenum) + "buf= " + str(bufsize) + "mul = " + str(bufmultiple) + "cores = " + core)
    sumfilename = "mxc_" + str(maxcorenum) + "bf_" + str(bufsize) + "step_" + str(step) + "cr_" + core + ".txt"
    sum = open(sumfilename, "w")
    sum.write("runame,cores,buf,mul,minlat,mincore,maxlat,maxcore,avglat,totalBW\n") 
    if(options.core):
        corelist.append(core)
    elif(sweep):
        corehi = (step - 1)
        corelo = 0
        for i in range(int(maxcorenum/step)):
            core = str(corelo) + "-" + str(corehi)
            corehi += step
            corelo += step
            corelist.append(core)
    #cmdlist = list()

    for cpu in (corelist):
       for i in range(1, bufmultiple):
           c = cpu
           buf = bufsize*i
           itr = options.iter
           ser = "-s" if options.ser  else  ""
           #print("./" + options.cmd + " -c " + c + " -m " + str(buf) + " -i " + i + " " + ser)

           cmdline = "./" + options.cmd + " -c " + c + " -m " + str(buf) + " -i " + itr + " " + ser
           runname = c + "_" + str(buf) + ".log"
           sum.write(runname + "," + c + "," + str(buf) + "," + str(bufmultiple) + ",")
           outfile = open(runname, "w")
           os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
           process = subprocess.Popen(cmdline, stdout=outfile, shell=True)
           process.wait()
           
           outfile.close()
           print(cmdline +  " run is complete ")
           with open(runname) as out:
              data = dict()
              for line in out:
                  if line.find("Latency of thread") > -1:
                      core = line.split()[3]
                      lat = line.split()[5]
                      data[core]=lat
                  if line.find("Total memory BW across all") > -1:
                      totalBW = line.split()[7]
           df = pd.DataFrame(list(data.items()), columns=['core', 'lat'])
           df[['lat']] =  df[['lat']].apply(pd.to_numeric)
           minlat = df['lat'].min()
           mincore = df.query('lat == @minlat')['core'].item()
           maxlat = df['lat'].max()
           maxcore = df.query('lat ==  @maxlat')['core'].item()
           avglat = df['lat'].mean()
           sum.write(str( minlat) + "," + str(mincore) + "," + str(maxlat) + "," + str(maxcore) + "," + str(avglat) + "," + str(totalBW) + "\n")
           os.system("mv " + runname + " ./Log/")




       













