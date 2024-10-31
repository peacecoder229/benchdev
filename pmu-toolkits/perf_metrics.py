#!/usr/bin/env python

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
from perf_monitor.monitor.perf_monitor import PerCoreLinuxPerfMonitor
from perf_monitor.reporter import *
import platform


def get_opts():
    """
    read user params

    :return: option object
    """
    parser = optparse.OptionParser()
    parser.add_option("-s", "--formula-setting", dest="setting",
                      default="dafault.xml",
                      help="formula setting file, XML formatted", )

    parser.add_option("-m", "--metric", dest="metric",
                      help="Metric for monitor", default="cpi")

    parser.add_option("-d", "--duration", dest="duration",
                      help="monitoring duration",
                      default="60")

    parser.add_option("-p", "--pid", dest="pid",
                      help="keep monitoring when a process alive",
                      default="0")

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

    # eventlist = set(reduce(lambda a, b: a.events + b.events, metric))

    # initial the monitor and start workload if needed.
    if options.pid != "0":
        cmd = "wait %s" % options.pid
    else:
        if platform.system() is "Windows":
            cmd = "timeout /t %s " % options.duration
        else:
            cmd = "sleep %s" % options.duration

    monitor = PerCoreLinuxPerfMonitor(cmd=cmd, event_list=eventlist,
                                      interval=float(options.interval),
                                      cores=options.cores)

    monitor.start_workload()

    # start to read telemetries from monitor

    for current_value in monitor.start_monitor():
        final_results = {}
        for m in metric:
            try:
                final_results[m.name] = m.get_result(current_value)
            except ZeroDivisionError:
                final_results[m.name] = "inf"

        yield final_results


if __name__ == '__main__':
    option = get_opts()
    monitor = start(option)

    if option.output is not None:
        ExcelReporter(monitor, option.output)
    else:
        for i in monitor:
            print i
