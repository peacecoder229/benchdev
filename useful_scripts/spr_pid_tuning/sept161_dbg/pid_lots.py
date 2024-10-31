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


def multi_plot_prim_sec(title, row=1, col=1, prim=None, sec=None, figsize=None):  

    baseline = {'type' : 'plot' , 'ls' : '-', 'lw' : '5', 'lm' : 'H', 'msz' : 18, 'font' : 30, 'bbox' : '{"x" : 0.95, "y" : 0.85}', 'loc' : 'upper right', 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'addtext' : None , 'addtextbox' : None, 'ylim' : None, 'yscale' : None, 'tag' : None} 
    basebar = {'type' : 'bar', 'width' : 0.3 , 'bbox' : '{"x" : 0.95, "y" : 0.35}', 'loc' : 'upper right', 'font' : 24, 'bbox' : '{"x" : 0.95, "y" : 0.85}', 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'updatebottom' : None, 'addtext' : None, 'addtextbox' : None, 'addoffset' : None , 'ylim' : None, 'yscale' : None, 'barlabel' : None, 'tag' : None}
    basemetric = { 'sortby' : None, 'xlabel' : 'Index', 'xvar' : 'index', 'rowrange' : None }
    sizex = int(figsize.split(",")[0])
    sizey = int(figsize.split(",")[1])
    if row == 1 and col == 1:
        fig, ax0 = plt.subplots(nrows=row, ncols=col, figsize=(sizex,sizey))
        plot = 1
        ax0sec = ax0.twinx() if sec else None
    elif (row == 1 and col == 2) or (row == 2 and col == 1):
        fig, [ax0, ax1] =  plt.subplots(nrows=row, ncols=col, figsize=(sizex,sizey))
        plot = 2
        ax0sec = ax0.twinx() if sec else None
        ax1sec = ax1.twinx() if sec else None
    elif (row == 2 and col == 2):
        fig, [[ax0, ax1], [ax2, ax3]] =  plt.subplots(nrows=row, ncols=col, figsize=(sizex,sizey))
        plot = 4

        ax0sec = ax0.twinx() if sec else None
        ax1sec = ax1.twinx() if sec else None
        ax2sec = ax2.twinx() if sec else None
        ax3sec = ax3.twinx() if sec else None
    else:
        print("Error in axis config\n")
        exit(1)



    finalmetlist = list()
    for n in range(plot):
        color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        pri_list = prim[n]
        for p in pri_list:
            #print(type(p))
            plotaxis = eval("ax%s" %(n))
            print("metric is %s\n" %(p))
            metlist = p['met'].split(",")
            metlistlen = len(metlist)
            off = 0
            offsetlist = offsetlist = [round((off + i*0.1),1) for i in range(0, metlistlen )]
            plottype = p['type'] if p['type'] else line
            updatelist = json.loads(p['updatelist']) if p['updatelist'] else None
            csv = p['csv']
            if csv:
                print("prepare metric property collection for primary\n")
            else:
                print("No file given \n")
                exit(1)
            i=0
            #color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
            legendbox = p['bbox'] if  p['bbox'] else None 
            for metric in metlist:
                coloridx = i%7
                met = "%s" %(metric)
                m = dict()
                m.update(basemetric)
                m.update(axis = plotaxis)
                m.update(met = met)
                m.update(csv =  csv)
                if plottype == 'bar':
                    m.update(basebar)
                else:
                    m.update(baseline)
                if m['tag']:
                    m.update(tag =  p['tag'])
                else:
                    m.update(tag = met.upper())
                if updatelist:
                    m.update(updatelist)
                else:
                    pass
                #print(m)
                #below values suppplied outside updatelist.. they have to be expicitly updated here.
                if p['bbox']:
                    m.update(bbox = legendbox)
                else:
                    pass
                if 'addtextbox' in p:
                    m.update(addtextbox = p['addtextbox'])
                else:
                    pass
                if metric == metlist[-1]:
                    m.update(setaxis = "yes")
                else:
                    pass
                print(updatelist.keys())
                if "color" in updatelist:
                    print("Color assigned is %s\n" %(updatelist["color"]))
                else:
                    m.update(color = color[coloridx])

                    print("Color assigned is %s\n" %(color[coloridx]))
                #below for bartype plots width is fixed to 0.1
                #and if addoffset is passed from main then only a single offet is passed to all metricss
                #else each metric extra offset is added  for example 0.1 , then 0.2 , then 0.3 so that each metric plotted next to each prev ones. width is also changed to 0.1 .
                #TBD make width and offset as values that can be updated .. offsetset list should be crated from passed value and  if 'addoffset' in updatelist: line need to be changed. 
                if metlistlen > 1 and plottype == 'bar':
                    if 'addoffset' in updatelist:
                        print(updatelist['addoffset'])
                        pass
                    else:
                        print("Updating bar offset to %s\n" %(offsetlist[i]))
                        m.update(addoffset = offsetlist[i])
                        m.update(width = 0.1)
                finalmetlist.append(m)
                i += 1
                print("I = %s and color index is %s\n" %(i, coloridx))
            #print(finalmetlist)

            
        if(sec):
            sec_list = sec[n]
            for p in sec_list:
                secaxis = eval("ax%ssec" %(n))
                metlist = p['met'].split(",")
                plottype = p['type'] if p['type'] else line
                updatelist = json.loads(p['updatelist']) if p['updatelist'] else None
                csv = p['csv']
                if csv:
                    print("prepare metric property collection for secondary\n")
                else:
                    print("No file given \n")
                    exit(1)
                k = 3
                legendbox = p['bbox'] if  p['bbox'] else None 
                for metric in metlist:
                    seccoloridx = k%7
                    print("sec color idx is %s and color is %s\n" %(k, color[seccoloridx]))
                    met = "%s" %(metric)
                    ms = dict()
                    ms.update(basemetric)
                    ms.update(axis = secaxis)
                    ms.update(tag = met.upper())
                    ms.update(met = met)
                    ms.update(csv =  csv)
                    if p['bbox']:
                        m.update(bbox = legendbox)
                    else:
                        pass
                    if plottype == 'bar':
                        ms.update(basebar)
                    else:
                        ms.update(baseline)
                    if updatelist:
                        ms.update(updatelist)
                    else:
                        pass
                    if metric == metlist[-1]:
                        ms.update(setaxis = "yes")
                    else:
                        pass
                    ms.update(color = color[seccoloridx])
                    if p['bbox']:
                        print("Updating bbox to %s\n" %(p['bbox']))
                        ms.update(bbox = p['bbox'])
                    else:
                        pass
                    #print(ms)
                    finalmetlist.append(ms)
                    k += 1
        n += 1


    #print(finalmetlist)

    for metric in finalmetlist:
        for k,v in metric.items():
            pass
            #print("key is %s and value=%s\n" %(k, v))

    flex_plot(finalmetlist)
    titlefont =  baseline['font'] + 6
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=titlefont)
    plt.tight_layout()
    title = title.replace("\n", "")
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)



def single_plot_prim_sec(title, prim=None, sec=None):  

    baseline = {'type' : 'plot' , 'ls' : '-', 'lw' : '5', 'lm' : 'H', 'msz' : 18, 'font' : 24, 'bbox' : '{"x" : 0.95, "y" : 0.85}', 'loc' : 'upper right', 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'addtext' : None } 
    basebar = {'type' : 'bar', 'width' : 0.3 , 'bbox' : '{"x" : 0.95, "y" : 0.35}', 'loc' : 'upper right', 'font' : 24, 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'updatebottom' : None, 'addtext' : None, 'addoffset' : None }
    basemetric = { 'sortby' : None, 'xlabel' : 'Index', 'xvar' : 'index' }

    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(75,15))
    ax1sec = ax1.twinx() if sec else None

    finalmetlist = list()
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    for p in prim:
        metlist = p['met'].split(",")
        plottype = p['type'] if p['type'] else line
        updatelist = json.loads(p['updatelist']) if p['updatelist'] else None
        csv = p['csv']
        if csv:
            print("prepare metric property collection for primary\n")
        else:
            print("No file given \n")
            exit(1)
        i=0
        for metric in metlist:
            coloridx = i%7
            met = "%s" %(metric)
            m = dict()
            m.update(basemetric)
            m.update(axis = ax1)
            m.update(tag = met.upper())
            m.update(met = met)
            m.update(csv =  csv)
            if plottype == 'bar':
                m.update(basebar)
            else:
                m.update(baseline)
            if updatelist:
                m.update(updatelist)
            else:
                pass
            #print(m)
            if metric == metlist[-1]:
                 m.update(setaxis = "yes")
            else:
                pass
            print(updatelist.keys())
            if "color" in updatelist:
                print("Color assigned is %s\n" %(updatelist["color"]))
            else:
                m.update(color = color[coloridx])
            finalmetlist.append(m)
            i += 1
            #print(finalmetlist)

            
    if(sec):        
        for p in sec:
            metlist = p['met'].split(",")
            plottype = p['type'] if p['type'] else line
            updatelist = json.loads(p['updatelist']) if p['updatelist'] else None
            csv = p['csv']
            if csv:
                print("prepare metric property collection for secondary\n")
            else:
                print("No file given \n")
                exit(1)
            k = 3
            for metric in metlist:
                seccoloridx = k%7
                print("sec color idx is %s and color is %s\n" %(k, color[seccoloridx]))
                met = "%s" %(metric)
                ms = dict()
                ms.update(basemetric)
                ms.update(axis = ax1sec)
                ms.update(tag = met.upper())
                ms.update(met = met)
                ms.update(csv =  csv)
                if plottype == 'bar':
                    ms.update(basebar)
                else:
                    ms.update(baseline)
                if updatelist:
                    ms.update(updatelist)
                else:
                    pass
                if metric == metlist[-1]:
                    ms.update(setaxis = "yes")
                else:
                    pass
                ms.update(color = color[seccoloridx])
                #print(ms)
                finalmetlist.append(ms)
                k += 1


    #print(finalmetlist)

    for metric in finalmetlist:
        for k,v in metric.items():
            pass
            #print("key is %s and value=%s\n" %(k, v))

    flex_plot(finalmetlist)
    fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
    plt.tight_layout()
    plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)






def flex_overlay_across_4_corners(title, filepat, sweeplist):

            '''
            filepat  with variable
            sweeplist consist of array of that variable. here we we pass a sweeplist of 4 values
            each value is substitured in the file to get teh file name. All metrics from that file
            is plotted on one of the four / or multiple subplots

            takes four datafiles and plots them in four subplots.
            For each datafile we define four metrics. each of them can be eaither a bar of line.
            and each drawing style can be overwritten over basestyle
            '''




            baseline = {'type' : 'plot' , 'ls' : '-', 'lw' : '5', 'lm' : 'H', 'msz' : 18, 'font' : 24, 'bbox' : '{"x" : 0.95, "y" : 0.85}', 'loc' : 'upper right', 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'addtext' : None } 
            basebar = {'type' : 'bar', 'width' : 0.3 , 'bbox' : '{"x" : 0.95, "y" : 0.35}', 'loc' : 'upper right', 'font' : 24, 'color' : 'g', 'setleg' : 'no', 'setaxis' : 'no', 'updatebottom' : None, 'addtext' : None, 'addoffset' : None }


            '''
            metric1 = { 'tag' : 'HP_BW' , 'met' : 'hpbw',  'xvar' : 'setp' , 'sortby' : 'setp', 'xlabel' : 'HWDRC SetPoint', 'ylabel' : 'BW in MB/s'} 
            metric2 = { 'tag' : 'HP_LAT' , 'met' : 'hplat',  'xvar' : 'setp' , 'sortby' : 'setp', 'xlabel' : 'HWDRC SetPoint', 'ylabel' : 'HP Lat in nS' } 
            
            metric4 = { 'tag' : 'LP_BW' , 'met' : 'lpbw',  'xvar' : 'setp' , 'sortby' : 'setp', 'xlabel' : 'HWDRC SetPoint', 'ylabel' : 'BW in MB/s'} 
            metric5 = { 'tag' : 'LP_LAT' , 'met' : 'lplat',  'xvar' : 'setp' , 'sortby' : 'setp', 'xlabel' : 'HWDRC SetPoint', 'ylabel' : 'Lat in nS' } 
            metric3 = { 'tag' : 'SYS_BW' , 'met' : 'sysbw',  'xvar' : 'setp' , 'sortby' : 'setp', 'xlabel' : 'HWDRC SetPoint', 'ylabel' : 'BW in MB/s'} 
            
            '''
            metric1 = { 'tag' : 'HP_BW' , 'met' : 'hpbw',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : 'BW in MB/s'} 
            metric2 = { 'tag' : 'HP_LAT' , 'met' : 'hplat',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : 'HP Lat in nS' } 
            
            metric4 = { 'tag' : 'LP_BW' , 'met' : 'lpbw',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : 'BW in MB/s'} 
            metric5 = { 'tag' : 'LP_LAT' , 'met' : 'lplat',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : 'Lat in nS' }
            
            '''
            metric1 = { 'tag' : 'HP_BW' , 'met' : 'hpbw',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : '% BW and Lat Change'} 
            metric2 = { 'tag' : 'HP_LAT' , 'met' : 'hplat',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : '% BW and Lat Change' } 
            
            metric4 = { 'tag' : 'LP_BW' , 'met' : 'lpbw',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : '% BW and Lat Change'} 
            metric5 = { 'tag' : 'LP_LAT' , 'met' : 'lplat',  'xvar' : 'case' , 'sortby' : None, 'xlabel' : 'HPcores_LPcores_pat', 'ylabel' : '% BW and Lat Change' }
            '''
            #create dicts with csv file names and axis

            fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(nrows=2, ncols=2, figsize=(75,15))
            ax1sec = ax1.twinx()
            ax2sec = ax2.twinx()
            ax3sec = ax3.twinx()
            ax4sec = ax4.twinx()

            #filelist1 = ["mlc_hwdrc_32c_lplat/32Chpd_%s_lpd_0.csv" %(hpd) for hpd in [0, 100, 250, 500]]
            #filelist2 = ["mlc_hwdrc_20clplat/20Chpd_%s_lpd_0.csv" %(hpd) for hpd in [0, 100, 250, 500]]
            
            
            #datainfo = {'ax1' : data1, 'ax1sec' : data2}
            datainfo = dict()
            data = dict()
            i = 1
            #filepat = '"mlc_hwdrc_32c_lplat/32Chpd_%s_lpd_0.csv" %(hpd)'
            #for hpd in [0, 100, 250, 500]:

            
            #plot them on primary as well as sec

            for hpd in sweeplist:
                f = eval(filepat)
                plottag = "HP MLC Delay %s" %(hpd)
                ax = eval("ax%s" %(i))
                axsec = eval("ax%ssec" %(i))
                metric1.update(basebar)
                metric1.update(csv = f, setleg = 'yes', axis=ax, updatebottom='yes', lw=7)
                #metric1.update(csv = f, setleg = 'yes', axis=ax, lw=7)
                
                metric4.update(basebar)
                metric4.update(color = 'r')
                metric4.update(csv = f, setleg = 'yes', axis=ax, setaxis = 'yes', addtext = plottag, addoffset=0.0)

                metric2.update(baseline)
                metric2.update(csv = f, setleg = 'yes', axis=axsec)
                metric2.update(ls = '--')
                
                metric5.update(baseline)
                metric5.update(csv = f, color = 'r', setleg = 'yes', axis=axsec, setaxis = 'yes')
                #print("Type for pri is " + str(type(prim)))
                #datainfo = [metric1, metric2, metric4, metric5]
                flex_plot([metric1, metric2, metric4, metric5])
                i += 1
                #print(metric1)
            
            
            #plots only on primary axis
            '''
            for hpd in sweeplist:
                f = eval(filepat)
                plottag = "HP MLC Delay %s" %(hpd)
                ax = eval("ax%s" %(i))
                metric1.update(basebar)
                #metric1.update(csv = f, setleg = 'yes', axis=ax, updatebottom='yes', lw=7)
                metric1.update(csv = f, setleg = 'yes', axis=ax, lw=7)
                
                metric4.update(basebar)
                metric4.update(color = 'r')
                metric4.update(csv = f, setleg = 'yes', axis=ax, setaxis = 'yes', addtext = plottag, addoffset=0.0)

                metric2.update(baseline)
                metric2.update(csv = f, setleg = 'yes', axis=ax)
                metric2.update(ls = '--')
                
                metric5.update(baseline)
                metric5.update(csv = f, color = 'r', setleg = 'yes', axis=ax)
                #print("Type for pri is " + str(type(prim)))
                #datainfo = [metric1, metric2, metric4, metric5]
                flex_plot(metric1, metric2, metric4, metric5)
                i += 1
                #print(metric1)
            '''
            
            fig.suptitle(title, horizontalalignment='center', verticalalignment='top',  fontsize=30)
            plt.tight_layout()
            plt.savefig("%s.pdf" %(title), dpi=300, transparent=True,pad_inches=0)

def flex_plot(kwargs, bottom = None):
    for info in kwargs:
        print(info['met'])
        #print(info)
        if info['met']:
            metric =  info['met']
        else:
            print("Metric to plot not given\n")
            exit(1)
 
        if info['csv']:
            csv =  info['csv']
        else:
            print("CSVfile not given\n")
            exit(1)
        
        plottype = info['type'] if info['type'] else 'plot'
        sortby = info['sortby'] if info['sortby'] else None
        BBOX = json.loads(info['bbox'])
        if info['addtextbox']:
            addtextbox = json.loads(info['addtextbox'])
        else:
            addtextbox = { 'x' : 0.5 , 'y' : 0.75}
        xvar = info['xvar'] if info['xvar'] else 'index'
        color = info['color'] if info['color'] else 'g'
        tag = info['tag'] if info['tag'] else None
        legend = info['tag'] if info['tag'] else None
        xlabel = info['xlabel'] if info['xlabel'] else None
        ylabel = info['ylabel'] if info['ylabel'] else None
        yscale = info['ylim'] if  info['ylim'] else None
        yscaletype = info['yscale'] if  info['yscale'] else None
        if 'barlabel' in info:

            barlabel = info['barlabel']
        else:
            barlabel = None

        if info['rowrange']:
            rangelo, rangehi = info['rowrange'].split(",")
            rangelo = int(rangelo)
            rangehi = int(rangehi)
        else:
            pass

        ax = info['axis']
        if plottype == 'bar' or  plottype == 'barh':
            offset =  info['addoffset'] if info['addoffset'] else 0	
            width = float(info['width'])
            if width is None:
                print("Width not defined for bar chart\n")
                exit(1)

            df = pd.read_csv(csv, sep=",", header=0)

            if info['rowrange']:
                df = df.iloc[rangelo:rangehi]
            else:
                pass

            if sortby:
                df.sort_values([sortby], inplace=True)

            if xvar == 'index':
                xvar = df.index
            else:
                xvar = df[xvar]

            if offset is None:
                 print("Offset  not defined for bar chart\n")
                 exit(1)
            else:
                offset_var = np.array(len(df.index) * [float(offset)] )
                print("Offset is %s\n" %(offset))
                print(offset_var)

        #print(df) update bottom for first bar
            if plottype == 'bar':
                if bottom is None:
                    bottom = np.zeros(len(df.index))
            #plot = eval("ax.%s" %(plottype))
                print(df.index)
                x_var = np.arange(len( df.index))
                df.index = np.add(x_var, offset_var)
                print(x_var)
                print(df[metric])
                ax.bar(df.index, df[metric], bottom=bottom, label = tag, color = color, width=width)

                if barlabel:
                    print(df[metric])
                    for i in df.index:
                        hieght =  round(float(df.at[i, metric]), 2)
                        print("Hieght is %s\n" %(hieght))
                        ax.text(i, hieght, '%s' %(hieght), fontsize=30,  ha='center', va='bottom')
                else:
                    pass

                if info['updatebottom']:
                    bottom = df[metric] + bottom
                else:
                    pass
            elif  plottype == 'barh':
                ax.barh(df.index, df[metric], label = tag, color = color, width=width)
            #In case of plot type provide font,ls,lw,lm, loc, bbox.x and bbox.y
            if info['setleg'] == "yes":
                loc = info['loc'] if info['loc'] else 'upper right'
                font = info['font'] if info['font'] else 20
                bbox = (BBOX['x'], BBOX['y']) if info['bbox'] else (.75, 0.75)  
                ax.legend(bbox_to_anchor=bbox, loc=loc, fontsize=font)
            else:
                pass
            if info['setaxis'] == 'yes':
                ax.set_ylabel(ylabel, fontsize=font)
                ax.set_xlabel(xlabel, fontsize=font)
                if yscale:
                    ylo, yhi = yscale.split(",")
                    yhi = round(float(yhi), 1)
                    ylo = round(float(ylo), 1)
                    print("Top is %s and Bot is %s\n" %(yhi, ylo))

                    ax.set_ylim(bottom=ylo, top=yhi)
                else:
                    pass
                if yscaletype:
                    ax.set_yscale(yscaletype)
                else:
                    pass
                #ax.xticks(ticks = df.index, labels = xvar)
                #ticks_loc = ax.get_xticks().tolist()
                #ax.set_xticklabels(xvar)
                ax.set_xticks(df.index)
                ax.set_xticklabels(xvar)
                #plt.xticks(ticks = df.index, labels = xvar)
                plt.setp(ax.get_xticklabels(), rotation=90, fontsize=font)
                plt.setp(ax.get_yticklabels(), fontsize=font)
            else:
                pass
            
            if info['addtext']:
                #ax.annotate(info['addtext'], xy=(150,120000), xycoords='data', va='center', ha='center', fontsize=28, bbox=dict(boxstyle="round", fc="w"))
                print("textbox x= %s\t and textbox y= %s\n" %(addtextbox['x'], addtextbox['y']))
                ax.annotate(info['addtext'], xy=(addtextbox['x'], addtextbox['y']), xycoords='axes fraction', va='center', ha='center', fontsize=font, color='b', bbox=dict(boxstyle="round", fc="w"))
            else:
                pass
        #for k,v in info.items():
        #    print("Info key : %s has a value %s\n" %(k, v))      
        #print("metric is %s and CSV file is %s xaxis is %s and chartype if %s and sort by is %s\n" %(info['met'], info['csv'], info['xvar'], info['type'], info['sortby'] ))
                

        if plottype == 'plot':
            df = pd.read_csv(csv, sep=",", header=0)

            if info['rowrange']:
                df = df.iloc[rangelo:rangehi]
            else:
                pass

            if sortby:
                df.sort_values([sortby], inplace=True)

            if xvar == 'index':
                xvar = df.index
            else:
                xvar = df[xvar]

            #plot = eval("ax.%s" %(plottype))
            lm = info['lm'] if info['lm'] else 'o'
            ls = info['ls'] if  info['ls'] else '-'
            lw = info['lw'] if  info['lw'] else 3
            ms = info['msz'] if info['msz'] else 3
            ax.plot(df.index, df[metric], label = tag, color = color,  marker = lm, markersize=ms, ls=ls, lw=lw)
            if info['setleg'] == "yes":
                loc = info['loc'] if info['loc'] else 'upper right'
                font = info['font'] if info['font'] else 20
                bbox = (BBOX['x'], BBOX['y']) if info['bbox'] else (.75, 0.75)  
                ax.legend(bbox_to_anchor=bbox, loc=loc, fontsize=font)
            else:
                pass
            if info['setaxis'] == 'yes':
                ax.set_ylabel(ylabel, fontsize=font)
                ax.set_xlabel(xlabel, fontsize=font)
                if yscale:
                    ylo, yhi = yscale.split(",")
                    yhi = round(float(yhi), 1)
                    ylo = round(float(ylo), 1)

                    ax.set_ylim(bottom=ylo, top=yhi)
                else:
                    pass
                if yscaletype:
                    ax.set_yscale(yscaletype)
                else:
                    pass
                print("setting xlabel =%s\n" %(xlabel))
                ax.set_xticks(df.index)
                ax.set_xticklabels(xvar)
                #plt.xticks(ticks = df.index, labels = xvar)
                plt.setp(ax.get_xticklabels(), rotation=90, fontsize=font)
                plt.setp(ax.get_yticklabels(), fontsize=font)
            else:
                pass
            
            if info['addtext']:
                #ax.annotate(info['addtext'], xy=(0.5,0.75), xycoords='data', va='center', ha='center', bbox=dict(boxstyle="round", fc="w"))
                ax.annotate(info['addtext'], xy=(addtextbox['x'], addtextbox['y']), xycoords='axes fraction', va='center', ha='center', fontsize=font, color='b', bbox=dict(boxstyle="round", fc="w"))
            else:
                pass
             

            





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


    lstyle = ['-', '--', '-.', ':', '']
    dataset=dict()
    filepat1='"mlc_hwdrc_32c_lplat/32Chpd_%s_lpd_0.csv" %(hpd)'
    filepat2='"mlc_hwdrc_20clplat/20Chpd_%s_lpd_0.csv" %(hpd)'
    filepat3='"mlc_pat_core/20Chpd_%s_lpd_0.csv" %(hpd)'
    title1="16C HP and 16C LP BW and lat impact with Setpoint Change and LP Delay =0"
    title3="HP and LP groups BW  & latency  perf without HWDRC(sp=255)  across LP pat and HP & LP core count change"
    #title3="% Chnage in HP and LP BW and latency with HWDRC across LP pat and differentHP a& LP  core counts  LP Delay =0"
    title2="12C HP and 8C LP BW and lat impact with Setpoint Change and LP Delay =0"
    #dataset[title1]=filepat1
    #dataset[title2]=filepat2
    dataset[title3]=filepat3
    sweeplist = [0, 100, 250, 500]
    #for t, f in dataset.items():
        #flex_overlay_plots(t, f, sweeplist)


    primdict1 = dict()
    primdict2 = dict()

    #primdict1 = { "csv" : "nginx_ffmpeg/ngx_680000_16_16000_15_1_ff_2_16.csv", "met" : "hputil,lputil" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC SetPoint", "ylabel" : "latency in (mS)", "setleg" : "yes"}' }
    #primdict1 = { "csv" : "AWS_res/singlevm_running_c5.9xlarge.csv", "met" : "Pavg" , "type" : "bar", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "vmid", "addtext" : "1 EC2 runs, 6 EC2 idle", "color" : "g"}' }
    #secdict1 = {"bbox" : '{"x" : 0.95, "y" : 0.85}', "csv" : "AWS_res/sevenvm_running.csv", "met" : "p90_var" , "type" : "plot", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "%Normalized Variation", "setleg" : "yes", "xvar" : "vmid", "yscale" : "log"}' }
    #c54xp90 = { "csv" : "AWS_res/12vm_c5.4xlarge.csv", "met" : "P90" , "type" : "bar", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "vmid",  "addtext" : "P90 Latency in each of 12 C5.x4large VMs",  "addoffset" : "0.0", "yscale" : "log", "ylim" : "1,10000"}' }
    c54xp90 = { "csv" : "AWS_res/12vm_c5.4xlarge.csv", "met" : "P90" , "type" : "bar", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "vmid",  "addtext" : "P90 Latency in each of 12 C5.x4large VMs",  "addoffset" : "0.0", "ylim" : "1,10000"}' }
    #c59xp90 = { "csv" : "AWS_res/12vm_c5.9xlarge.csv", "met" : "P90" , "type" : "bar", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "vmid",  "addtext" : "P90 Latency in each of 12 C5.x9large VMs",  "addoffset" : "0.0", "yscale" : "log", "ylim" : "1,10000"}' }
    c59xp90 = { "csv" : "AWS_res/12vm_c5.9xlarge.csv", "met" : "P90" , "type" : "bar", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "vmid",  "addtext" : "P90 Latency in each of 12 C5.x9large VMs",  "addoffset" : "0.0", "ylim" : "1,10000"}' }
# "ylim" : "0,120"
    #ngxp99 = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "nginxp99,memcachp99" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0", "yscale" : "log"}' }
    ngxp99only = {"bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/ngxin_con_rps_sweep_sorted.csv", "met" : "ngxp99" , "type" : "line", "updatelist" : '{"xlabel" : "RPS_CON_Iteration", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0", "lw" : "9", "font" : "36"}' }
    #ngxp99 = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "nginxp99,memcachp99" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0", "yscale" : "log"}' }
    #ngxp99comp = { "csv" : "nginx_ffmpeg_mc/res_old/nginx_comp_t.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0", "yscale" : "log"}' }
    #ngxp99 = { "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/nginx_ffmpeg_comp.csv", "met" : "ngxp99,ngxp99::ff_16,ngxp99::ff_4,ngxp99::ff_8" , "type" : "bar", "updatelist" : '{"xlabel" : "Measurement No", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "Iter", "lw" : "10", "font" : "36" }' }
    ngxp99comp = { "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/res_old/nginx_comp_t.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "Agressor Combo and HWDRC Setpoint", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36" }' }
    ngxp99_combo = { "addtextbox" : '{"x" : 0.5, "y" : 0.75}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/res_old/nginx_comp_t.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "Agressors and HWDRC Config", "ylabel" : "nginx p99 lateency in (ms)", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Nginx on 8 cpu, Memcache on 8cpu ; FFMPG on 16cpu\\n ffmpg with DRC shows some improvments \\n DRC with MC  and ffmpg combo TBD"}' }
    wrkld_combo_ff = { "addtextbox" : '{"x" : 0.5, "y" : 0.75}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "mix_run/combned_normalized_t_ff_t.csv", "met" : "specjbb,nginx,mcache" , "type" : "bar", "updatelist" : '{"xlabel" : "HWDRC_setting_and_IterationNo", "ylabel" : "latency variation normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor FFMPG on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n Both groups are thottled with same priority \\n normalized p99 latency of workloads plotted on yaxis "}' }
    mix_np_pr_combo_stress = { "addtextbox" : '{"x" : 0.75, "y" : 0.5}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/stressmem_ngx_jbb_iter_res_mod.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "Workload_HWDRC-Configuration", "ylabel" : "latency variation normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor stressapp on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n normalized p99 latency of workloads plotted on yaxis "}' }
    mix_np_pr_combo_stress_avg = { "addtextbox" : '{"x" : 0.75, "y" : 0.75}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/stressmem_avg_sum.csv", "met" : "AVG-normalized-p99lat" , "type" : "bar", "updatelist" : '{"xlabel" : "Workload_HWDRC-Configuration", "ylabel" : "Average of latency variations normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "barlabel" : "yes" , "addtext" : "Agressor stressapp on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n Average normalized p99 latency of workloads plotted on yaxis "}' }
    mix_np_pr_combo_ff_avg = { "addtextbox" : '{"x" : 0.75, "y" : 0.75}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/ff_avg_sum.csv", "met" : "AVG-normalized-p99lat" , "type" : "bar", "updatelist" : '{"xlabel" : "Workload_HWDRC-Configuration", "ylabel" : "Average of latency variations normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "barlabel" : "yes" , "addtext" : "Agressor FFMPEG on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n Average normalized p99 latency of workloads plotted on yaxis "}' }
    mix_np_pr_combo_ff = { "addtextbox" : '{"x" : 0.75, "y" : 0.6}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/ff_ngx_jbb_iter_res_mod.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "Workload_HWDRC-Configuration", "ylabel" : "latency variation normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor FFMPG on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n normalized p99 latency of workloads plotted on yaxis "}' }
    #mix_np_pr_combo_ff_rdt = { "addtextbox" : '{"x" : 0.75, "y" : 0.6}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/nginx_ff_ecs_cases.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "DRC_or_RDT_Configuration", "ylabel" : "latency variation normalized to minimum latency with 100%MBA", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor FFMPG on group1 with 16 cpu ; NGINX on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n RDT_mb.. % same MBA set for both group1 and group2 \\n normalized p99 latency of workloads plotted on yaxis ", "width" : "0.15", "addoffset" : "0.15"}' }
    mix_np_pr_combo_ff_rdt = { "addtextbox" : '{"x" : 0.75, "y" : 0.6}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/nginx_ff_ecs_cases.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "DRC_or_RDT_Configuration", "ylabel" : "latency variation normalized to minimum latency with 100%MBA", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor FFMPG on group1 with 16 cpu ; NGINX on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n RDT_mb.. % same MBA set for both group1 and group2 \\n normalized p99 latency of workloads plotted on yaxis "}' }
    mix_np_pr_combo_ff_rdt_sm = { "addtextbox" : '{"x" : 0.75, "y" : 0.6}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "hwdrc_final_plot/nginx_ff_ecs_cases_stressM.csv", "met" : "itr1,itr2,itr3,itr4,itr5" , "type" : "bar", "updatelist" : '{"xlabel" : "DRC_or_RDT_Configuration", "ylabel" : "latency variation normalized to minimum latency with 100%MBA", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor StressApp on group1 with 16 cpu ; NGINX on group2 with 16 cpus\\n mixpr:workloads high priority agressor low priority  \\n nopr: workloads and agressor both same priority \\n RDT_mb.. % same MBA set for both group1 and group2 \\n normalized p99 latency of workloads plotted on yaxis "}' }
    wrkld_combo_stress = { "addtextbox" : '{"x" : 0.75, "y" : 0.6}', "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "mix_run/combned_normalized_t_stres_t.csv", "met" : "specjbb,nginx,mcache" , "type" : "bar", "updatelist" : '{"xlabel" : "HWDRC_setting_and_IterationNo", "ylabel" : "latency variation normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "yscale" : "log", "barlabel" : "yes" , "addtext" : "Agressor StressApp on group1 with 16 cpu ; Workloads on group2 with 16 cpus\\n Both groups are thottled with same priority \\n normalized p99 latency of workloads plotted on yaxis "}' }
    ngxdbg = { "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "mix_run/debug_nginx.csv", "met" : "hputil,hpipc,lputil,lpipc" , "type" : "bar", "updatelist" : '{"xlabel" : "Workload", "ylabel" : "latency variation normalized to minimum latency without DRC", "setleg" : "yes", "xvar" : "case", "lw" : "10", "font" : "36", "barlabel" : "yes" }' }
    #ngxp99 = { "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/ngx_sum.csv", "met" : "ngxp99,ngxp99::ffmpg,ngxp99::mc,ngxp99::ffmpg::mc" , "type" : "bar", "updatelist" : '{"xlabel" : "Measurement No", "ylabel" : "NGINX P99 latency in (mS)", "setleg" : "yes", "xvar" : "Iter", "lw" : "10", "font" : "32" , "ylim" : "0,11"}' }
    mcp99 = { "bbox" : '{"x" : 0.65, "y" : 0.85}', "csv" : "nginx_ffmpeg_mc/mc_sum.csv", "met" : "mcp99,mcp99::ffmpg,mcp99::ngx::ffmpg,mcp99::ngx" , "type" : "bar", "updatelist" : '{"xlabel" : "Measurement No", "ylabel" : "Memcached P99 latency in (mS)", "setleg" : "yes", "xvar" : "Iter", "lw" : "10", "font" : "32" , "ylim" : "0,11" }' }
    tmpngxp99 = '{ "csv" : "nginx_ffmpeg_mc/nginx_lat_setp_sum_iter%s.csv", "met" : "nginxp99,memcachp99" , "type" : "line", "updatelist" : \'{"xlabel" : "HWDRC_SetPoint", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "setp",  "addoffset" : "0.0", "yscale" : "log", "lw" : "7", "ls" : "%s", "rowrange" : "0,7"}\' }'
    #ngxp99only = '{ "csv" : "nginx_ffmpeg_mc/ngxin_con_rps_sweep_sorted.csv", "met" : "nginxp99" , "type" : "line", "updatelist" : \'{"xlabel" : "RPS_CON_Iteration", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0", "lw" : "9", "font" : "36"}\' }'
    #mcp99 = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "memcachp99" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0"}' }
    ngxutil = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "nginxutil,memcachutil,ffmpegutil" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "CoreGroup % CPU Util", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.0"}' }
    tmpngxutil = '{ "csv" : "nginx_ffmpeg_mc/nginx_lat_setp_sum_iter%s.csv", "met" : "nginxutil,memcachutil,ffmpegutil" , "type" : "line", "updatelist" : \'{"xlabel" : "HWDRC_SetPoint", "ylabel" : "CoreGroup %% CPU Util", "setleg" : "yes", "xvar" : "setp",  "addoffset" : "0.0", "lw" : "7", "ls" : "%s", "rowrange" : "0,7"}\' }'
    memcachutil = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "memcachutil" , "type" : "bar", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "CoreGroup % CPU Util", "setleg" : "yes", "xvar" : "case",  "addoffset" : "0.3"}' }
    mpgutil = { "csv" : "nginx_ffmpeg_mc/ngx_mc_ffmeg_sum.csv", "met" : "ffmpegutil" , "type" : "bar", "updatelist" : '{"xlabel" : "HWDRC_SetPoint_NGINX_Connections", "ylabel" : "CoreGroup % CPU Util", "setleg" : "yes", "xvar" : "case",  "addoffset" : "-0.3"}' }
    #primtdict1 = { "met" : "p50,p75,p99" , "type" : "line", "updatelist" : '{"xlabel" : "HWDRC SetPoint", "ylabel" : "latency in (mS)", "setleg" : "yes"}' }
    #secdict2 = {"bbox" : '{"x" : 0.95, "y" : 0.85}', "csv" : "AWS_res/sevenvm_running_c5.9xlarge.csv", "met" : "p90_var" , "type" : "plot", "updatelist" : '{"xlabel" : "EC2-Instance-ID", "ylabel" : "% Normalized Variation", "setleg" : "yes", "xvar" : "vmid", "yscale" : "log"}' }
    
    #secdict1 = { "csv" : "nginx_ffmpeg/nginx_lat_setp_sum_mod.csv", "met" : "QPS,RPS" , "type" : "line", "updatelist" : '{"xlabel" : "SETP_FF%", "ylabel" : "Total timeouts in 2 minutes", "setleg" : "yes", "xvar" : "case", "ls" : "--", "bbox" : \'{"x" : "0.95", "y" : "0.85"}\'}' }
    #secdict1 = {"bbox" : '{"x" : 0.65, "y" : 0.85}',  "csv" : "nginx_ffmpeg/nginx_lat_setp_sum_iter1.csv", "met" : "QPS,RPS" , "type" : "line", "updatelist" : '{"xlabel" : "SETP", "ylabel" : "Requested and Executed QPS", "setleg" : "yes", "xvar" : "case", "ls" : "--"}' }

    #primdict_tmp = '{ "csv" : "nginx_ffmpeg/nginx_lat_setp_sum_iter%s.csv", "met" : "p99" , "type" : "line", "updatelist" : \'{"xlabel" : "SETP_LPshare_CON", "ylabel" : "latency in (mS)", "setleg" : "yes", "xvar" : "case", "lw" : "7" , "ls" : "%s"}\' }'
    #primdict2tmp = '{ "csv" : "nginx_ffmpeg/nginx_lat_setp_sum_iter%s.csv", "met" : "hputil,lputil" , "type" : "line", "updatelist" : \'{"xlabel" : "SETP_LPShare_CON", "ylabel" : "CPU Util in Percentage ", "setleg" : "yes", "xvar" : "case", "lw" : "7", "ls" : "%s"}\' }'
    #primdict2tmp = '{ "csv" : "nginx_ffmpeg/nginx_lat_setp_sum_iter%s.csv", "met" : "hputil" , "type" : "line", "updatelist" : \'{"xlabel" : "SETP_LPShare_CON", "ylabel" : "CPU Util in Percentage ", "setleg" : "yes", "xvar" : "case", "lw" : "7", "ls" : "%s"}\' }'
     
    pid_out = '{"bbox" : None, "csv" : "/home/pid_tuning/sept161_dbg/8_16_0_161_%s.csv", "met" : "pid_out" , "type" : "line", "updatelist" : \'{"xlabel" : "sampleTime", "ylabel" : "Integer TimeWindow value", "setleg" : "yes", "xvar" : "sampleTime",  "addoffset" : "0.0", "lw" : "7", "ls" : "%s", "rowrange" : "5000,30000"}\' }'
    pid_budget = '{"bbox" : None, "csv" : "/home/pid_tuning/sept161_dbg/8_16_0_161_%s.csv", "met" : "pid_budget" , "type" : "line", "updatelist" : \'{"xlabel" : "sampleTime", "ylabel" : "Integer TimeWindow value", "setleg" : "yes", "xvar" : "sampleTime",  "addoffset" : "0.0", "lw" : "7", "ls" : "%s", "rowrange" : "5000,30000"}\' }'
    ewma_out = '{"bbox" : None, "csv" : "/home/pid_tuning/sept161_dbg/8_16_0_161_%s.csv", "met" : "ewma_out" , "type" : "line", "updatelist" : \'{"xlabel" : "sampleTime", "ylabel" : "Integer TimeWindow value", "setleg" : "yes", "xvar" : "sampleTime",  "addoffset" : "0.0", "lw" : "7", "ls" : "%s", "rowrange" : "5000,30000"}\' }'
    rpqocc = '{"bbox" : None,  "csv" : "/home/pid_tuning/sept161_dbg/8_16_0_161_%s.csv", "met" : "rpqocc" , "type" : "line", "updatelist" : \'{"xlabel" : "sampleTime", "ylabel" : "Integer TimeWindow value", "setleg" : "yes", "xvar" : "sampleTime",  "addoffset" : "0.0", "lw" : "7", "ls" : "%s", "rowrange" : "5000,30000"}\' }'
    pid_out_list = list()
    pid_budget_list = list()
    ewma_out_list = list()
    rpqocc_list = list()
    listofprimarymetrics = list()
    listofprim2metrics = list()
    ewma_val = enumerate(["1", "4", "6", "8", "9", "13", "15"])
    for i,v in ewma_val:
        i = i % 5
        pid_out_tmp = eval(pid_out %(v, lstyle[i]))
        pid_bdg_tmp = eval(pid_budget %(v, lstyle[i]))
        ewma_tmp = eval(ewma_out %(v, lstyle[i]))
        rpqocc_tmp = eval(rpqocc %(v, lstyle[i]))
        pid_out_list.append(pid_out_tmp)
        pid_budget_list.append(pid_bdg_tmp)
        ewma_out_list.append(ewma_tmp)
        rpqocc_list.append(rpqocc_tmp)

        #print(listofprimarymetrics)


    
    multi_plot_prim_sec("PID Controller Charecterization \n", row=2, col=2, prim=[pid_out_list, pid_budget_list, ewma_out_list, rpqocc_list], sec=None, figsize="60,45")

    #multi_plot_prim_sec("Agressor FFMPEG: wrklds NGINX and SpecJBB;  ECS no-priority vs mixpriority vs no DRC \n", row=1, col=1, prim=[[mix_np_pr_combo_ff]], sec=None, figsize="60,45")
    multi_plot_prim_sec("Agressor FFMPEG: NGINX perf SLA variation with DRC(mixpr &nopr) vs noDRC vs static MBA(nopr)\n", row=1, col=1, prim=[[mix_np_pr_combo_ff_rdt]], sec=None, figsize="60,45")
    multi_plot_prim_sec("Agressor StressApp: NGINX perf SLA variation with DRC(mixpr &nopr) vs noDRC vs static MBA(nopr)\n", row=1, col=1, prim=[[mix_np_pr_combo_ff_rdt_sm]], sec=None, figsize="60,45")
    #multi_plot_prim_sec("Agressor StressApp: Avg p99 lat reduction with  ECS no-priority vs mixpriority vs no DRC \n", row=1, col=1, prim=[[mix_np_pr_combo_stress_avg]], sec=None, figsize="60,45")
    #multi_plot_prim_sec("Agressor FFMPEG: Avg p99 lat reduction with  ECS no-priority vs mixpriority vs no DRC \n", row=1, col=1, prim=[[mix_np_pr_combo_ff_avg]], sec=None, figsize="60,45")


    #bbox is for legend.. for text bx still a fixed offset is being used. ax.annotate(info['addtext'], xy=(0.6,0.75), xycoords='axes fraction', va='center', ha='center', fontsize=28, color='b', bbox=dict(boxstyle="round", fc="w"))
