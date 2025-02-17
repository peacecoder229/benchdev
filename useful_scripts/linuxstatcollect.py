#!/usr/bin/env python3
import subprocess
import sys
import time
import re
import signal
import queue
'''
arg1: cpus that needs to be moitored
arg2: ts in seconds for mpstat
arg3: no of iterations
arg4: outfile name
'''


def get_cores(c):
    cpu = list()
    seg = c.split(",")
    for s in seg:
        low,high = s.split("-")
        if low == None or high == None:
            cpu.append(s)
        else:
            for i in range(int(low), int(high)+1):
                cpu.append(i)

    return len(cpu)



def execute(cmd):
    cpustat = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    cpustat.wait()

    for l in cpustat.stdout.readlines():
        yield l.decode('utf-8')
        #print(l.decode('utf-8'))

def executestdout_nowait(buf, header):
    #out = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True , universal_newlines=True)
    for l in iter(buf.readline, ""):
        if not re.search(rf"{re.escape(header)}", l):
            yield l
#Note above nore conversion into utf-8 done as universal_newlines is true


def process_vmstat():
    data = dict()
    vmstatcmd="vmstat 1"
    try:
        vmstatprocess = subprocess.Popen(vmstatcmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        print("VMstat launched\n")
    except:
        print("CMD launch not Successful")
    headerpat = "procs -----------memory-"
    outl = executestdout_nowait(vmstatprocess.stdout, headerpat)
    print(outl)
    while vmstatprocess.poll() is None:
        #print("VM stat running\n")
        try:
            l = next(outl)
            print(l)
            l = l.rstrip().lstrip()
            if re.search(r'buff', l):
                metrics = re.split(r'\s+', l)
                for m in metrics:
                    data[m] = list()

            else:
                vals = re.split(r'\s+', l)
                for i in range(len(vals)):
                    data[metrics[i]].append(vals[i])
        except StopIteration:
            pass
        except KeyboardInterrupt:
            print("End of VMstat datacollection")    
            print(data)
            vmstatprocess.send_signal(signal.SIGINT)
            sys.exit()
            #pass
    #print("End of VMstat datacollection")
    #print(data)
    #vmstatprocess.send_signal(signal.SIGINT)


    




def process_vmstat_queue(size=10):
    data = dict()
    vmstatcmd="vmstat 1"
    try:
        vmstatprocess = subprocess.Popen(vmstatcmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        print("VMstat launched\n")
    except:
        print("CMD launch not Successful")
    headerpat = "procs -----------memory-"
    outl = executestdout_nowait(vmstatprocess.stdout, headerpat)
    print(outl)
    while vmstatprocess.poll() is None:
        #print("VM stat running\n")
        try:
            l = next(outl)
            print(l)
            l = l.rstrip().lstrip()
            if re.search(r'buff', l):
                metrics = re.split(r'\s+', l)
                for m in metrics:
                    data[m] = queue.Queue(maxsize=size)

            else:
                vals = re.split(r'\s+', l)
                for i in range(len(vals)):
                    if not data[metrics[i]].full():
                        data[metrics[i]].put(vals[i])
                    else:
                        itm=data[metrics[i]].get()
                        print("Removed item is %s\n" %(itm))
                        data[metrics[i]].put(vals[i])

        except StopIteration:
            pass
        except KeyboardInterrupt:
            print("End of VMstat datacollection")    
            for key in data:
                print(key)
                print(list(data[key].queue))
            vmstatprocess.send_signal(signal.SIGINT)
            sys.exit()
            #pass
    #print("End of VMstat datacollection")
    #print(data)
    #vmstatprocess.send_signal(signal.SIGINT)






def get_cpu_stat(corestat):

    '''
    arg1: cpus that needs to be moitored
    arg2: ts in seconds for mpstat
    arg3: no of iterations
    arg4: outfile name
    '''
    for i in execute(corestat):
        cpuno = i.split()[1]
        usr = i.split()[3]
        ker = i.split()[5]
        #print("cpuno " + cpuno + " usr " + usr + " ker " + ker) 
        out.write("cpuno " + cpuno + " usr " + usr + " ker " + ker + "\n") 


#with open("metricfile", "r") as out:
#    for l in out:
#        print(l.split())
def get_numa_stat(nstat):

    count = 1
    N0_prev = dict()
    N1_prev = dict()
    N0_cur = dict()
    N1_cur = dict()

    N0_prev['local'] =  0
    N1_prev['local'] =  0
    N0_prev['rem'] = 0
    N1_prev['rem'] =  0

    while(count < iteration):

        G = execute(nstat)
        local=next(G)
        remote=next(G)
        N0_cur['local'] = int(local.split()[1])
        N1_cur['local'] = int(local.split()[2])

        N0_cur['rem'] = int(remote.split()[1])
        N1_cur['rem'] = int(remote.split()[2])



    #print("Socket0 local =" + str(N0_cur['local'] - N0_prev['local']) + "Socket1 local =" + str(N1_cur['local'] - N1_prev['local']))
        out.write("Socket0 local =" + str(N0_cur['local'] - N0_prev['local']) + "  Socket1 local =" + str(N1_cur['local'] - N1_prev['local']) + "\n")
        out.write("Socket0 rem =" + str(N0_cur['rem'] - N0_prev['rem']) + "  Socket1 rem =" + str(N1_cur['rem'] - N1_prev['rem']) + "\n")

        N0_prev['local'] =  N0_cur['local']
        N1_prev['local'] =  N1_cur['local']
        N0_prev['rem'] = N0_cur['rem']
        N1_prev['rem'] =  N1_cur['rem']
    #print(next(G))
    #print(next(G))
        time.sleep(1)
        count+=1
    out.close()    

if __name__ == "__main__":

    if(len(sys.argv) < 1):
        print(get_cpu_stat.__doc__)
    elif sys.argv[1] == "vmstat":
        #process_vmstat()
        process_vmstat_queue(5)
    else:
        cores = sys.argv[1]
        ts = sys.argv[2]
        iteration = int(sys.argv[3])
        outname = sys.argv[4]

        out = open(outname, "w")


#cmd = "mpstat  -u -P 0-1,24-25 1 2 | tail -n 4 | awk \'{print $2 " " $3 + $4}\'"
        cpucount = get_cores(cores)
        corestat = "mpstat  -u -P " + cores + " " + ts +  "  " + str(iteration) +  "  | tail -n " + str(cpucount)
#print(corestat)
#out = open("metricfile", "w")
#cpustat = subprocess.Popen(cmd, stdout=out, shell=True)

        nstat = "numastat | tail -n 2"
        #get_cpu_stat(corestat)
