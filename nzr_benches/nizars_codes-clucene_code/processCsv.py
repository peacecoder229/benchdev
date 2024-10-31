#!/usr/bin/python3

import pandas as pd
import numpy as np
import argparse
import subprocess
import os

# run the experiment with specified no clients and server
def runExperiment(noOfClients, noOfServers):
    clientPerServer = int(noOfClients/ noOfServers);
    noOfThreads = 1
    runTime = 1
    topk = 5
    serverPort = 8080
    serverIp = "127.0.0.1"
    searchType = "c"

    # fist run servers
    for serverId in range(noOfServers):
        # formatted string marked by "f" at the front, supported in pytohn 3
        cmd = f"./server {noOfThreads} {runTime} {topk} {searchType} {serverIp} {serverId} {serverPort} {clientPerServer}"
        print(cmd)
        # process = subprocess.Popen(cmd.split())
        os.system(cmd)

    for clientId in range(noOfClients):
        cmd = f"./client {serverIp} {serverPort} {clientId} &"
        print(cmd)
        #process = subprocess.Popen(cmd.split())
        os.system(cmd)

    #os.system('wait')
    #Popen.wait()

def processLogs():
    print("Experment is done. Now processing logs.")


parser = argparse.ArgumentParser()
parser.add_argument("noOfServer", help = "Number of Servers", type = int)
parser.add_argument("noOfClient", help = "Number of Clients", type = int)
parser.add_argument("expCombinedFileName", help = "Name of experiment combined file")
parser.add_argument("runTime", help = "Experiment run time in minutes", type = int)

args = parser.parse_args()
noOfServer = args.noOfServer
noOfClient = args.noOfClient
expCombinedFileName = args.expCombinedFileName
runTime = args.runTime
clientPerServer = int(noOfClient/ noOfServer);

# there should be <noOfRuns> number of client and server
#clientNo = [2]
#serverNo = [1]
'''
for expNo in range(len(clientNo)):
    runExperiment(clientNo[expNo], serverNo[expNo])
    os.system('wait')
    processLogs()
'''

# combine the client and server logs
print("Finished running experiment. Processing logs now.")
serverId = 0
clientServerCombDfList = list()
for clientId in range(noOfClient):
    clientDf = pd.read_csv(f"Client_{clientId}_RTT.csv")
    serverDf = pd.read_csv(f"Server_{serverId}_Search_Queue_Delay.csv")
    result = pd.merge(serverDf, clientDf, on = 'QueryTag')
    clientServerCombDfList.append(result)
    
    if ((clientId+1) % clientPerServer == 0):
        serverId = serverId + 1

clientServerCombDf =  pd.concat(clientServerCombDfList)
clientServerCombDf.to_csv(f"Combined_Server_{noOfServer}_Client_{noOfClient}_Search_Queue_RTT.csv", index = False)

serverAvgQps = float("{0:.2f}".format(len(clientServerCombDf.index)/(60 * runTime * noOfServer)))
serverAvgSearchTime = float("{0:.2f}".format(clientServerCombDf["SearchLatency(us)"].mean()/noOfServer))
serverAvgQueueDelay = float("{0:.2f}".format(clientServerCombDf["Queue Latency(us)"].mean()/noOfServer))
clientAvgRTT = float("{0:.2f}".format(clientServerCombDf["RTT(us)"].mean()/noOfServer))

# write to the file
f = open(expCombinedFileName, "a")
f.write(f"\n{noOfClient}, {noOfServer}, {serverAvgQps}, {serverAvgSearchTime}, {serverAvgQueueDelay}, {clientAvgRTT}")

print("Done processing log.")

os.system("./cleanlog.sh")

'''
import commands
lsOut = commands.getstatusoutput("ls -t | grep Client_1 | head -1")
df_client = pd.read_csv(lsOut[1])
print(df_client.head())
'''
