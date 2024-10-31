#!/usr/bin/evn python

#
# Copyright (c) 2017 by Intel Corp
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

import optparse

from perf_monitor.formula.EDP_formula import EDPFormulaReader
# from monitor.emon_monitor import PerCoreEmonMonitor
from perf_monitor.monitor.base import FakeMonitor
from perf_monitor.reporter import *
import platform

from perf_monitor.monitor.file_monitor import DiskMonitor, NICMonitor


def get_opts():
    """
    read user params
    
    :return: option object 
    """
    parser = optparse.OptionParser()
    parser.add_option("-s", "--formula-setting", dest="setting",
                      default="default.xml",
                      help="formula setting file, XML formatted", )

    parser.add_option("-m", "--metric", dest="metric",
                      help="Metric for monitor",
                      default="cpi,kernel_cpi,L1D MPI (includes data+rfo w/ prefetches)")

    parser.add_option("-d", "--duration", dest="duration",
                      help="monitoring duration",
                      default="60")

    parser.add_option("-c", "--cores", dest="cores", help="CPU affinity",
                      default=None)

    parser.add_option("-o", "--output", dest="output", help="Dump to a file",
                      default=None)

    parser.add_option("-i", "--interval", dest="interval",
                      help="Calibration interval", default=1.0)

    (options, args) = parser.parse_args()

    return options


def start(options):
    # read all metrics from EDP configuration file
    reader = EDPFormulaReader(options.setting)
    all_metrics = reader.get_metric_list()

    # filter out the metric by user param
    metric = [all_metrics[i] for i in options.metric.split(",")]
    # metric = all_metrics[options.metric]

    # get the event counter name list for the metrics
    eventlist = []
    for m in metric:
        eventlist.extend(m.events)
    eventlist = list(set(eventlist))

    # task_manager = MonitoringTaskManager()
    # eventlist = set(reduce(lambda a, b: a.events + b.events, metric))

    # initial the monitor and start workload if needed.
    if platform.system() is "Windows":
        cmd = "timeout /t %s " % options.duration
    else:
        cmd = "sleep %s" % options.duration

    # for i in xrange(2):
    monitor1 = FakeMonitor(cmd=cmd, event_list=eventlist,
                           interval=float(options.interval),
                           cores=options.cores)
    monitor1.set_name("monitor_1")

    monitor2 = FakeMonitor(cmd=cmd, event_list=eventlist,
                           interval=float(options.interval),
                           cores=options.cores)
    monitor2.set_name("monitor_2")

    monitor3 = FakeMonitor(cmd=cmd, event_list=eventlist,
                           interval=float(options.interval),
                           cores=options.cores)
    monitor3.set_name("monitor_3")

    disk_monitor=DiskMonitor(cmd=cmd, event_list=eventlist,
                           interval=float(options.interval),
                           cores=options.cores)
    disk_monitor.set_name('disk_monitor')

    nic_monitor=NICMonitor(cmd=cmd, event_list=eventlist,
                           interval=float(options.interval),
                           cores=options.cores)
    nic_monitor.set_name('nic_monitor')

    monitor = monitor1 & monitor2 & monitor3 & disk_monitor & nic_monitor

    # task_manager.launch_monitor(name, monitor)

    # monitor.start_workload()

    # start to read telemetries from monitor

    # for name, timestamp, current_value in task_manager.get_telemetry():
    for final_results in monitor.start_monitor():

        if final_results['monitor'].startswith("monitor"):
            print final_results['monitor']

            for m in metric:
                try:
                    final_results[m.name] = m.get_result(final_results)
                except ZeroDivisionError:
                    final_results[m.name] = "inf"
        else:
            print "How did you do that?"

        yield final_results


if __name__ == '__main__':

    option = get_opts()
    monitor = start(option)

    if option.output is not None:
        ExcelReporter(monitor, option.output)
    else:
        PrintOut(monitor, option.output)
