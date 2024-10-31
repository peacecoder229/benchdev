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

import time
from base import MonitorBase


class StaticFileBase(MonitorBase):
    File = ""

    def start_workload(self, output_file=None):
        pass

    def start_monitor(self):
        while True:
            hmap = self.formatter(self.read_file())
            yield hmap
            time.sleep(self.Inteval)

    def read_file(self):
        with open(self.File, "r") as fd:
            return fd.readlines

    def formatter(self, content):
        return content


class DiskMonitor(StaticFileBase):
    File = "/proc/diskstats"

    def formatter(self, content):
        desc = (
            ("reads", 3), ("read_sectors", 5), ("read_ms", 6), ("writes", 7),
            ("write_sectors", 9), ("write_ms", 10), ("io_queue", 11),
            ("io_ms_weighted", 13)
        )
        hmap = {}
        for line in content:
            items = line.split()
            dev = items[2]
            for type, offset in desc:
                event_name = "%s.%s" % (dev, type)
                if len(self.EventList) is 0 or event_name in self.EventList:
                    hmap[event_name] = int(items[offset])
        return hmap


class NICMonitor(MonitorBase):
    File = "/proc/net/dev"

    def formatter(self, content):
        desc = (("recv_bytes", 1), ("recv_packets", 2), ("send_bytes", 9),
                ("send_packets", 10))

        hmap = {}
        for line in content:
            items = line.split()
            if items[0][-1] != ':':
                continue

            nic_name = items[0][:-1]
            for type, offset in desc:
                evnet_name = "%s.%s" % (nic_name, type)
                if len(self.EventList) is 0 or evnet_name in self.EventList:
                    hmap[evnet_name] = int(items[offset])
        return hmap


class CPUFrequncyMonitor(MonitorBase):
    File = "/sys/devices/system/cpu/cpu%s/frequncy/%s"

    Group = ['cpuinfo_min_freq', 'cpuinfo_max_freq', 'scaling_min_freq',
             'scaling_max_freq', 'cpuinfo_cur_freq']

    def read_file(self):
        telemetry = {}
        for i in self.EventList:
            metric, cpu = tuple(i.lower().splite("."))
            filename = self.File % (cpu, metric)
            with open(filename, "r") as fd:
                telemetry[i] = int(fd.read(32))

        return telemetry
