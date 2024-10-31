 #!/usr/bin/python3

import pandas as pd
import numpy as np
import argparse

print("Processing the combined logs now ......")

parser = argparse.ArgumentParser()
parser.add_argument("noOfServer", help = "Number of Servers", type = int)
parser.add_argument("noOfClient", help = "Number of Clients", type = int)
parser.add_argument("expCombinedFileName", help = "Name of experiment combined file")
parser.add_argument("runTime", help = "Experiment run time in minutes", type = int)
parser.add_argument("noOfThreads", help = "No of Searcher threads")

args = parser.parse_args()
noOfServer = args.noOfServer
noOfClient = args.noOfClient
expCombinedFileName = args.expCombinedFileName
runTime = args.runTime
noOfThreads = args.noOfThreads

searchStartDf = pd.read_csv("Server_Search_Start_Combine.log")
searchEndDf =  pd.read_csv("Server_Search_End_Combine.log")
searchStartEndDf = pd.merge(searchStartDf, searchEndDf, on = 'QueryTag')
searchDelay = searchStartEndDf['SearchEnd'] - searchStartEndDf['SearchStart']
searchDelayMean = float("{0:.2f}".format(searchDelay.mean()))* 1000

queueStartDf =  pd.read_csv("Server_Queue_Start_Combine.log")
queueEndDf = pd.read_csv("Server_Queue_End_Combine.log")
queueStartEndDf = pd.merge(queueStartDf, queueEndDf, on = 'QueryTag')
queueDelay = queueStartEndDf['QueueEnd'] - queueStartEndDf['QueueStart']
queueDelayMean = float("{0:.2f}".format(queueDelay.mean())) * 1000

rttDf = pd.read_csv("Client_Rtt_Combine.log")
rttMean = float("{0:.2f}".format(rttDf['RTT(us)'].mean()))

serverAvgQps = float("{0:.2f}".format(len(searchStartDf.index)/(60 * runTime)))

f = open(expCombinedFileName, "a")
f.write(f"\n{noOfThreads}, {serverAvgQps}, {searchDelayMean}, {queueDelayMean}, {rttMean}")
