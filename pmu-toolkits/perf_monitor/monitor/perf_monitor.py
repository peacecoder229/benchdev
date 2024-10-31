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

from base import MonitorBase


class LinuxPerfMonitor(MonitorBase):
    _monitor_command = "perf stat %s -a sleep %s 2>&1"

    extension_params = []

    def set_monitor_command(self):
        self.extension_params = []
        self.extension_params.append("-e %s" % ",".join(self.EventList))
        self.monitor_command = self._monitor_command % (
            " ".join(self.extension_params),
            self.Inteval)

    def formatter(self, content):
        """
        Convert stdout to dict

        :param content: stdout from ocperf
        :return: dict {event_name(lower case): value}
        """
        content = content.splitlines()
        telemetry = {}
        for i, row in enumerate(content[3:3 + len(self.EventList)]):
            row = filter(lambda x: x != "", row.split(" "))
            event_name = self.EventList[i].lower()
            telemetry[event_name] = float(row[0].replace(",", ""))

        return telemetry


class PerCoreLinuxPerfMonitor(LinuxPerfMonitor):
    Cores = None
    _monitor_command = "perf stat %s sleep %s 2>&1"

    def __init__(self, cmd, event_list=None, interval=1, cores=None):
        MonitorBase.__init__(self, cmd, event_list, interval)

        if cores is not None:
            self.set_cores(cores)

    def set_cores(self, cores):
        self.Cores = cores

    def set_monitor_command(self):
        self.extension_params = []
        if self.Cores is not None:
            self.extension_params.append("-C %s" % self.Cores)

        self.extension_params.append("-e %s" % ",".join(self.EventList))
        self.monitor_command = self._monitor_command % (
            " ".join(self.extension_params),
            self.Inteval)
