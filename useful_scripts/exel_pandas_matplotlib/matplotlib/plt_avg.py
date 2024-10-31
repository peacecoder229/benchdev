#!/usr/bin/env python3
import pandas as pd
import matplotlib
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_agregate(sum_file, met1, met2):
  #df = pd.read_csv(summary, header=0, index_col=False)
  df = pd.read_csv("Average_stat.txt", header=0, index_col=False)
  df['sp'] = df['sp'].apply(pd.to_numeric, errors='coerce')
  print(df.columns)
  df_sorted = df.sort_values(by=['pid', 'sp'],  ascending=[True, True])
  #df_sorted = df.sort_values(by=['sp'],  ascending=[True])
  print(df_sorted.columns)
  pid_met1 = df_sorted[met1]
  xval = df_sorted['p:i:d:sp']
  pid_met2 = df_sorted[met2]
  fig, ax1 = plt.subplots(figsize=(75,15))
  ax2 = ax1.twinx()
  ax1.plot(xval, pid_met1, Label = met1, color ='r', marker = 'o')
  ax1.set_xlabel("Kp:Ki:Kd:SetPoint", fontsize=24)
  plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
  plt.setp(ax1.get_yticklabels(), fontsize=20)
  #ax1.set_xticklabels("Kp:Ki:Kd:SetPoint", rotation=90, fontsize=1)
  ax1.set_ylabel(met1, fontsize=28)
  ax1.legend(bbox_to_anchor=(0.25, 0.75), loc='upper left', fontsize=20)
  ax2.plot(xval, pid_met2, Label = met2, color ='b', marker = 'x')
  plt.setp(ax2.get_yticklabels(), fontsize=20)
  #ax2.set_xticklabels("Kp:Ki:Kd:SetPoint", rotation=90, fontsize=4)
  ax2.set_ylabel(met2, fontsize=28)
  ax2.legend(bbox_to_anchor=(0.75, 0.75), loc='upper right', fontsize=20)
 # plt.xticks(rotation=90, fontsize=4)
  #plt.xticks(rotation='vertical')
  plt.tight_layout()
  #plt.rc('font', size=10)
  #plt.rc('xtick', labelsize=10)
  #plt.rc('ytick', labelsize=10)
  #plt.rcParams['xtick.labelsize'] = 'small'
  ax1.grid()
  ax2.grid()
  plt.savefig("%s_%s.png" %(met1, met2), dpi=300, transparent=True,pad_inches=0)


if __name__ == "__main__":
 plot_agregate("Average_stat.txt", "th_limit_os", "th_limit_avg")
 plot_agregate("Average_stat.txt", "rpq_occ_avg", "budget_avg")
