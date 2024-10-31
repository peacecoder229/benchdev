#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import re
import signal
import pandas as pd
import matplotlib
import numpy as np
from matplotlib import cm
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy.interpolate import griddata as gd
import json
'''
'-' solid line style
'--'    dashed line style
'-.'    dash-dot line style
':' dotted line style
'''


def primary_sec_overlay(title, **kwargs):
    fig, ax1 = plt.subplots(figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    ax2 = ax1.twinx()
    i = 0
    no = len(kwargs.keys())
    for csv, vals in kwargs.items():
        coloridx = i%7
        print("colors are %s and %s\n" %(color[coloridx], color[coloridx+1])) 
        df = pd.read_csv(csv, sep=",", header=0, index_col=None)
        met1, met2, xvar, tag = re.split(",", vals)
        ax1.plot(df[xvar], df[met1], label = met1 + "_" + tag, color = color[coloridx], marker = 'o')
        ax1.legend(bbox_to_anchor=(0.25, 0.85), loc='upper left', fontsize=24)
        ax2.plot(df[xvar], df[met2], Label = met2 + "_" + tag, color =color[coloridx+1], marker = 'x')
        ax2.legend(bbox_to_anchor=(0.75, 0.85), loc='upper right', fontsize=24)
        i += 2
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    ax1.set_xlabel(xvar, fontsize=24)
    plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    ax1.set_ylabel(met1, fontsize=28)
    plt.setp(ax2.get_yticklabels(), fontsize=20)
    ax2.set_ylabel(met2, fontsize=28)
    plt.tight_layout()
    plt.savefig("%s_%s_%s.pdf" %(title, met1, met2), dpi=300, transparent=True,pad_inches=0)
    
def primary_sec_overlay_4plots(title, **kwargs):
    fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(nrows=2, ncols=2, figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    i = 0
    k =1
    no = len(kwargs.keys())
    for csv, vals in kwargs.items():
        coloridx = i%4
        ax = eval("ax%s" %(k))
        print("ax objecttype is %s\n" %(type(ax)))
        axsec = ax.twinx()
        print("colors are %s and %s\n" %(coloridx, coloridx+1)) 
        print("colors are %s and %s\n" %(color[coloridx], color[coloridx+1])) 
        df = pd.read_csv(csv, sep=",", header=0, index_col=None)
        df.sort_values(['hpbw'], inplace=True)
        met1, met2, met3, xvar, tag = re.split(",", vals)
        ax.plot(df[xvar], df[met1], label = met1 + "_" + tag, color = color[coloridx], marker = 'o')
        ax.legend(bbox_to_anchor=(0.1, 0.85), loc='upper left', fontsize=24)
        ax.plot(df[xvar], df[met2], label = met2 + "_" + tag, color = color[coloridx+1], marker = 'o')
        ax.legend(bbox_to_anchor=(0.1, 0.85), loc='upper left', fontsize=24)
        axsec.plot(df[xvar], df[met3], Label = met3 + "_" + tag, color =color[coloridx+2], marker = 'x')
        axsec.legend(bbox_to_anchor=(0.95, 0.85), loc='upper right', fontsize=24)
        
        ax.set_xlabel(xvar, fontsize=24)
        plt.setp(ax.get_xticklabels(), rotation=90, fontsize=20)
        plt.setp(ax.get_yticklabels(), fontsize=20)
        ax.set_ylabel(met1, fontsize=28)
        plt.setp(axsec.get_yticklabels(), fontsize=20)
        axsec.set_ylabel(met3, fontsize=28)
        #i += 3
        k += 1
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    plt.tight_layout()
    plt.savefig("%s_%s_%s_%s.pdf" %(title, met1, met2, met3), dpi=300, transparent=True,pad_inches=0)

def overlay_4plots(title, kwargs1, kwargs2):
    fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(nrows=2, ncols=2, figsize=(75,15))
    ax1sec = ax1.twinx()
    ax2sec = ax2.twinx()
    ax3sec = ax3.twinx()
    ax4sec = ax4.twinx()

    func_prim_sec_4plots(kwargs1, ax1, ax2, ax3, ax4, ax1sec, ax2sec, ax3sec, ax4sec, None, lstyle='--', width=6)
    func_prim_sec_4plots(kwargs2, ax1, ax2, ax3, ax4, ax1sec, ax2sec, ax3sec, ax4sec, "yes", lstyle='-', width=6)



    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    plt.tight_layout()
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)

def overlay_4plots_multiple(title, dictofplots, sortby = None):
    fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(nrows=2, ncols=2, figsize=(75,15))
    ax1sec = ax1.twinx()
    ax2sec = ax2.twinx()
    ax3sec = ax3.twinx()
    ax4sec = ax4.twinx()
    style = ['-', '--', ':']
    i = 0
    for key in dictofplots:
        infodict = json.loads(dictofplots[key])
        print(type(infodict))
        print(infodict)
        if i == 0:
            func_prim_sec_4plots(infodict, ax1, ax2, ax3, ax4, ax1sec, ax2sec, ax3sec, ax4sec, sortby, None, lstyle=style[i], width=6)
            i += 1
        else:
            func_prim_sec_4plots(infodict, ax1, ax2, ax3, ax4, ax1sec, ax2sec, ax3sec, ax4sec, sortby, "yes", lstyle=style[i], width=6)
            i += 1
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    plt.tight_layout()
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)
def func_prim_sec_4plots(kwargs, ax1, ax2, ax3, ax4, ax1sec, ax2sec, ax3sec, ax4sec, sortby, secondplot=None, lstyle='-', width=5):
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    i = 0
    k =1
    no = len(kwargs.keys())
    for csv, vals in kwargs.items():
        coloridx = i%4
        ax = eval("ax%s" %(k))
        axsec = eval("ax%ssec" %(k))
        print("ax objecttype is %s\n" %(type(ax)))
        print("colors are %s and %s\n" %(coloridx, coloridx+1)) 
        print("colors are %s and %s\n" %(color[coloridx], color[coloridx+1])) 
        df = pd.read_csv(csv, sep=",", header=0, index_col=None)
        #df.sort_values(['hpbw'], inplace=True)
        df.sort_values([sortby], inplace=True)
        met1, met2, met3, xvar, tag = re.split(",", vals)
        ax.plot(df[xvar], df[met1], label = met1 + "_" + tag, color = color[coloridx], marker = 'o', ls=lstyle, lw=width)
        ax.plot(df[xvar], df[met2], label = met2 + "_" + tag, color = color[coloridx+1], marker = 'o', ls=lstyle, lw=width)
        axsec.plot(df[xvar], df[met3], Label = met3 + "_" + tag, color =color[coloridx+2], marker = 'x', ls=lstyle, lw=width)
        if secondplot:
            pass
        else:
            ax.legend(bbox_to_anchor=(0.1, 0.85), loc='upper left', fontsize=24)
            axsec.legend(bbox_to_anchor=(0.95, 0.85), loc='upper right', fontsize=24)
            ax.legend(bbox_to_anchor=(0.1, 0.85), loc='upper left', fontsize=24)
            ax.set_xlabel(xvar, fontsize=24)
            plt.setp(ax.get_xticklabels(), rotation=90, fontsize=20)
            plt.setp(ax.get_yticklabels(), fontsize=20)
            ax.set_ylabel(met1, fontsize=28)
            plt.setp(axsec.get_yticklabels(), fontsize=20)
            axsec.set_ylabel(met3, fontsize=28)
        #i += 3
        k += 1

def primary_overlay(title, **kwargs):
    fig, ax1 = plt.subplots(figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    i = 0
    no = len(kwargs.keys())
    for csv, vals in kwargs.items():
        coloridx = i%7
        print("colors are %s and %s\n" %(color[coloridx], color[coloridx+1])) 
        df = pd.read_csv(csv, sep=",", header=0, index_col=None)
        met1, xvar, tag = re.split(",", vals)
        ax1.plot(df[xvar], df[met1], label = tag, color = color[coloridx], marker = 'o')
        ax1.legend(bbox_to_anchor=(0.25, 0.85), loc='upper left', fontsize=24)
        i += 1
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    ax1.set_xlabel(xvar, fontsize=24)
    plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    ax1.set_ylabel(met1, fontsize=28)
    plt.tight_layout()
    plt.savefig("%s_%s.pdf" %(title, met1), dpi=300, transparent=True,pad_inches=0)
    
def multi_overlay(title, **kwargs):
    fig, [ax1, ax2] = plt.subplots(nrows=2, ncols=1, figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    #ax2 = ax1.twinx()
    i = 0
    no = len(kwargs.keys())
    for csv, vals in kwargs.items():
        coloridx = i%7
        print("colors are %s and %s\n" %(color[coloridx], color[coloridx+1])) 
        df = pd.read_csv(csv, sep=",", header=0, index_col=None)
        met1, met2, xvar, tag = re.split(",", vals)
        ax1.plot(df[xvar], df[met1], label = met1 + "_" + tag, color = color[coloridx], marker = 'o')
        ax1.legend(bbox_to_anchor=(0.25, 0.85), loc='upper left', fontsize=24)
        ax2.plot(df[xvar], df[met2], Label = met2 + "_" + tag, color =color[coloridx+1], marker = 'x')
        ax2.legend(bbox_to_anchor=(0.75, 0.85), loc='upper right', fontsize=24)
        i += 2
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    ax1.set_xlabel(xvar, fontsize=24)
    plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    ax1.set_ylabel(met1, fontsize=28)
    plt.setp(ax2.get_yticklabels(), fontsize=20)
    ax2.set_ylabel(met2, fontsize=28)
    plt.tight_layout()
    plt.savefig("%s_%s_%s.pdf" %(title, met1, met2), dpi=300, transparent=True,pad_inches=0)


def prim_multi_overlay_allcolumns(csv, title, yaxis = None,  xvar = None):
    fig, ax1 = plt.subplots(figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    mark = [ 'o', 'v', '^', 's', 'p', '*', 'P', '+', 'X', '1', '4']
    i = 0
    df = pd.read_csv(csv, sep=",", header=0)
    df = df.iloc[5:32]
    for col in df.columns:
        coloridx = i%7
        markidx = i%11
        print("color is %s column is %s\n" %(color[coloridx], col)) 
        #df = pd.read_csv(csv, sep=",", header=0)
        met1 = col
        xval = df[xvar] if xvar else df.index
        ax1.plot(xval, df[met1], label = col, color = color[coloridx], marker = mark[markidx])
        ax1.legend(bbox_to_anchor=(0.25, 0.85), loc='upper left', fontsize=24)
        i += 1
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    x_label = xvar if xvar else "Index"
    y_label = yaxis if yaxis else met1
    ax1.set_xlabel(x_label, fontsize=28)
    plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    plt.yticks(np.arange(0, 260, 20))
    ax1.set_ylabel(y_label, fontsize=28)
    plt.tight_layout()
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)

def prim_multi_overlay_allcolumns_xtag(csv, title, yaxis = None,  xvar = None, tablecsv = None):
    fig, ax1 = plt.subplots(figsize=(75,15))
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    mark = [ 'o', 'v', '^', 's', 'p', '*', 'P', '+', 'X', '1', '4']
    i = 0
    df = pd.read_csv(csv, sep=",", header=0, index_col=False)
    dftable = pd.read_csv(tablecsv, sep=",", header=0) if tablecsv else None


    df = df.iloc[0:280]
    plotcols = list()
    for c in df.columns:
        if c != xvar:
            plotcols.append(c)
    print(plotcols)
    for col in plotcols:
        coloridx = i%7
        markidx = i%11
        print("color is %s column is %s\n" %(color[coloridx], col)) 
        #df = pd.read_csv(csv, sep=",", header=0)
        met1 = col
        xval = df[xvar] if xvar else df.index
        ax1.plot(xval, df[met1], label = col, color = color[coloridx], marker = mark[markidx], markersize = 12, linewidth = 3)
        ax1.legend(bbox_to_anchor=(0.25, 0.85), loc='upper left', fontsize=24)
        i += 1
    
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    x_label = xvar if xvar else "Time in Seconds"
    y_label = yaxis if yaxis else met1
    ax1.set_xlabel(x_label, fontsize=28)
    plt.setp(ax1.get_xticklabels(), rotation=90, fontsize=20)
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    ax1.set_ylabel(y_label, fontsize=28)
    plt.tight_layout()
    
    dftable = pd.read_csv(tablecsv, sep=",", header=0) if tablecsv else None
    # Create table
    if tablecsv:
        cell_text = []
        for row in range(len(dftable)):
            cell_text.append(dftable.iloc[row])

        table = plt.table(cellText=cell_text, colLabels=dftable.columns, rowLabels=dftable.index, bbox=[0.35, 0.4, 0.55, 0.5], loc='upper right', fontsize=28)
        table.set_fontsize(24)
        #plt.table(cellText=cell_text, colLabels=dftable.columns, rowLabels=dftable.index,  loc='upper right', fontsize='x-large')
    else:
        pass

    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)

def threeD_plot(csv, title, xaxis, yaxis, zaxis):
    fig, ax1 = plt.subplots(figsize=(75,15), subplot_kw={"projection": "3d"})
    df = pd.read_csv(csv, sep=",", header=0)
    x1 = np.linspace(df[xaxis].min(), df[xaxis].max(), len(df[xaxis].unique()))
    y1 = np.linspace(df[yaxis].min(), df[yaxis].max(), len(df[yaxis].unique()))
    x2, y2 = np.meshgrid(x1, y1)
    z2 = gd((df[xaxis], df[yaxis]), df[zaxis], (x2, y2), method='cubic')
    
    #surf = ax1.scatter3D(df[xaxis], df[yaxis], df[zaxis], s=30, cmap=plt.hot(), marker = 'o')
    surf = ax1.plot_surface(x2, y2, z2, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    #ax1.set_zlim = (0, 300)
    #ax1.zaxis.set_major_locator()
    plt.xticks(df[xaxis])
    plt.yticks(df[yaxis])
    plt.setp(ax1.get_yticklabels(), fontsize=20)
    plt.setp(ax1.get_xticklabels(), fontsize=20)
    plt.setp(ax1.get_zticklabels(), fontsize=20)
    ax1.set_ylabel("CoreCount", fontsize=28)
    ax1.set_xlabel("Delay", fontsize=28)
    ax1.set_zlabel("RPQ Occupancy", fontsize=28)
    
    
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.tight_layout()
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)
    

if __name__ == "__main__":
            #datainfo = {"noRDT_csv/MC_hp_rdb_lp_noRDT.csv" : "hpipc,hputil,time,MC" , "withRDT_csv/MC_hp_rdb_lp_withRDT.csv":"hpipc,hputil,time,JBB"}
            #datainfo1 = {"HWDRC/16hpc_0hpd_16lpc.csv" : "hpbw,lpbw,hplat,lpdelay,hp-hi", "HWDRC/16hpc_500hpd_16lpc.csv" : "hpbw,lpbw,hplat,lpdelay,hplo", "HWDRC/16hpc_500hpd_0lpd.csv" : "hpbw,lpbw,hplat,lpcores,hplo", "HWDRC/16hpc_0hpd_0lpd.csv" : "hpbw,lpbw,hplat,lpcores,hp-hi"}
            #datainfo2 = {"mlc_noQOs/16hpc_0hpd_16lpc.csv" : "hpbw,lpbw,hplat,lpdelay,hp-hi", "mlc_noQOs/16hpc_500hpd_16lpc.csv" : "hpbw,lpbw,hplat,lpdelay,lptraffic-hplo", "mlc_noQOs/16hpc_500hpd_0lpd.csv" : "hpbw,lpbw,hplat,lpcores,hplo", "mlc_noQOs/16hpc_0hpd_0lpd.csv" : "hpbw,lpbw,hplat,lpcores,hp-hi"}
            #primary_sec_overlay_4plots("HP VM BW IMpact with LP core and LP delay", **datainfo)
            datainfo = dict()
            for lpd in ["250"]:
                info = "{"
                for hpd in ["0" , "100", "250", "500"]:
                    info = "%s\"HWDRC/hpd_%s_lpd_%s.csv\" : \"hpbw,lpbw,hplat,setp,hp-%s\" ," %(info, hpd, lpd, hpd)
                info = re.sub(r",$" , "}", info)
                datainfo[lpd] = info
            
            for lpd in datainfo:
                #print(datainfo[lpd])
                print(type(datainfo[lpd]))
            overlay_4plots_multiple("HP and LP BW lat impact with Setpoint Change and LP Delay =250", datainfo, "hpbw")
                    
            #overlay_4plots("HP VM BW IMpact with LP core and LP delay dashed", datainfo1, datainfo2)
            #primary_sec_overlay("Memcache__rocksDB", **datainfo)
            #prim_multi_overlay_allcolumns_xtag("data_csv/DRC_vs_noQoS.csv", "HP Workload %  IPC Improvement with HWDRC vs NoQoS", "IPC Delta in %", None, "data_csv/DRC_vs_noQoS_summary.csv")
            #prim_multi_overlay_allcolumns_xtag("data_csv/percentage_system_ipc_delta_DRC_vs_SWDRC.csv", "System level total IPC delta HWDRC vs SWDRC", "IPC Delta in %", None, "data_csv/percentage_system_ipc_delta_DRC_vs_SWDRC_summary.csv")
            #multi_overlay("Memcache_JBB_with_rocksDB", **datainfo)
            #prim_multi_overlay_allcolumns("withRDT_csv/hpipc_QoS.csv", "HP_workload_IPC_with_RDT")
            #prim_multi_overlay_allcolumns("Qos_vs_staticQoS_hpipc.csv", "HP_IPC_QoS-noQos", "IPC Delta in %")
            #prim_multi_overlay_allcolumns("DRC_CAT_vs_staticQoS_hpipc.csv", "HP_IPC_DRC-QoS", "IPC Delta in %")
            #prim_multi_overlay_allcolumns("drc_cat_vs_nocat_hpipc.csv", "HP_IPC_DRC_CAT-NoCAT", "IPC Delta in %")
            #prim_multi_overlay_allcolumns_xtag("HWDRC/cat_impcat_on_hpipc.csv", "Impact of CAT on top of MCLOS HWDRC", "Workload IPC", "cat")
            #prim_multi_overlay_allcolumns_xtag("cat_impact_percentage_delta_updated.csv", "CAT Allocation on top of MCLOS HWDRC", "% Workload IPC Change", "cat")
            #prim_multi_overlay_allcolumns("NoQoS_rpq_occ_summary.csv", "RPQ_Occupancy", "Total RPQ Occupancy in Socket 0") 
            #prim_multi_overlay_allcolumns("mlcrpqocc_summary.csv", "MLC RPQ_Occupancy", "Total RPQ Occupancy in Socket 0")
            #threeD_plot("mlc_dly_core_rpq_mean.csv", "RQP_OCC Avg vs core count and Delay", "delay", "cores", "mean()") 
