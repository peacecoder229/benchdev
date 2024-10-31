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

import re
import subprocess

from base import MonitorBase


class CPUInfo:
    """
    CPU mapping relation from EMON
    """
    _info = 0

    def __init__(self, info):
        # INFO = THREAD_ID << 24 + PACKAGE_ID << 16 + CORE_ID << 8 + IS_LOGICAL
        self._info = info

    @property
    def is_logical(self):
        return bool(self._info & 0x1)

    @property
    def core(self):
        return (self._info >> 8) & 0xff

    @property
    def core_idx(self):
        return (self._info >> 8) & 0xffff

    @property
    def socket(self):
        return (self._info >> 16) & 0xff

    @property
    def thread(self):
        return self._info >> 24


class MemoryChannelInfo:
    """
    Channel Info form Emon

    """

    _info = 0

    def __init__(self, info):
        # INFO = PACKAGE_ID << 6 + CONTROLLER_ID << 3 + CHANNEL_ID
        self._info = info

    @property
    def channel(self):
        return self._info & 0x7

    @property
    def controller(self):
        return (self._info >> 3) & 0x7

    @property
    def socket(self):
        return self._info >> 6


class EmonTelemetryRouter:
    """
    This is a class may help distinguish telemetries' level: system, socket,
        core, thread. And assemble telemetries to each cores by core ID
    """

    EmonCommand = "emon -v"
    CPUInfo = None
    MemoryInfo = None
    TelemetryType = 0x0

    # define 5 levels here,
    THREAD_BASED = 0x0
    CORE_BASED = 0x1
    SOCKET_BASED = 0x2
    SYSTEM_BASED = 0x3
    MEMORY_CHANNEL_BASED = 0x4

    Data = None

    def __init__(self, filename=None):
        """
        read core sets from system or configuration file

        :param filename: configuration file name
        """
        if filename is not None:
            with open(filename, "r") as fd:
                raw = fd.readlines()
        else:
            raw = subprocess.check_output(self.EmonCommand, shell=True)
            raw = raw.splitlines()

        self.get_cores_hierarchy(raw)
        self.get_memory_channel(raw)

    def get_cores_hierarchy(self, raw):
        regex = re.compile(r"^\s+\d{1,3}\s+\d{1,3}\s+\d{1,3}\s+\d{1}$")
        content = filter(regex.match, raw)

        def hierarchy_encode(row):
            row = row.split("\t\t")[1:]
            row = reduce(lambda a, b: int(b) + (int(a) << 8), row)
            return CPUInfo(row)

        self.CPUInfo = tuple(map(hierarchy_encode, content))

    def get_memory_channel(self, raw):
        regex = re.compile(r"^\s+\((\d{1})\/(\d{1})\/(\d{1,2})")
        # regex = re.compile(r"^\s+\((\d{1})\/\d{1}\/\d{1,2}")
        memory_channel = []

        for row in raw:
            match = regex.findall(row)
            if len(match) is 0:
                continue
            mapping = reduce(lambda a, b: int(b) + (int(a) << 3), match.pop())
            memory_channel.append(MemoryChannelInfo(mapping))

        self.MemoryInfo = tuple(memory_channel)

    def set_telemetry(self, data):
        """
        Lebel telemetries' level through vector length.

        :param data: list telemetries
        :return: None
        """
        self.Data = data
        # self.Data = filter(filter, data)
        length = len(self.Data)

        if length is 1:
            self.TelemetryType = self.SYSTEM_BASED
            return

        if length is len(self.CPUInfo):
            self.TelemetryType = self.THREAD_BASED
            return

        socket = set([i.socket for i in self.CPUInfo])
        # socket = set([i[1] for i in self.CPUHierarchyInfo])
        if length is len(socket):
            self.TelemetryType = self.SOCKET_BASED
            return

        core = set([i.core for i in self.CPUInfo])
        # thread = set([i[2] for i in self.CPUHierarchyInfo])
        if length is len(core):
            self.TelemetryType = self.CORE_BASED
            return

        if length is len(self.MemoryInfo):
            self.TelemetryType = self.MEMORY_CHANNEL_BASED
            buffer = [0.0] * len(socket)
            for channel, value in zip(self.MemoryInfo, self.Data):
                socket = channel.socket
                buffer[socket] += value

            self.Data = buffer
            return

    def router(self, thread_id):
        """
        Do the routing

        :param thread_id: int
        :return:  mix, telemetry for this thread
        """
        if self.TelemetryType is self.THREAD_BASED:
            return self.Data[thread_id]

        if self.TelemetryType is self.SYSTEM_BASED:
            return self.Data[0]

        if self.TelemetryType is self.SOCKET_BASED:
            mapping = self.CPUInfo[thread_id].socket
            return self.Data[mapping]

        if self.TelemetryType is self.CORE_BASED:
            mapping = None
            if False is self.CPUInfo[thread_id].is_logical:
                # for a physical core, return back
                mapping = thread_id
            else:
                # for a logical core, find the physical
                # get full core name
                core_label = self.CPUInfo[thread_id].core_idx
                for i in self.CPUInfo:
                    if i.core_idx is core_label and not i.is_logical:
                        mapping = i.socket
                        break

            return self.Data[mapping]

        if self.TelemetryType is self.MEMORY_CHANNEL_BASED:
            mapping = self.CPUInfo[thread_id].socket
            return self.Data[mapping]

    def __getitem__(self, item):
        return self.router(item)

    def to_list(self):
        return [self.router(i) for i in range(len(self.CPUInfo))]

    def __str__(self):
        return str(self.to_list())


class EmonMonitor(MonitorBase):
    data_identifier = re.compile(r"^[A-Z][A-Z0-9.:_]+")
    _monitor_command = "emon -t%s -C %s "

    def __init__(self, cmd, event_list=None, interval=1):
        MonitorBase.__init__(self, cmd, event_list, interval)

        # initial a router before calibration started
        self.router = EmonTelemetryRouter()

    def set_monitor_command(self):
        # emon -t1 -C CPU_CLK_UNHALTED.REF,INST_RETIRED.ANY
        self.monitor_command = self._monitor_command % (
            self.Inteval, ",".join(self.EventList)
        )

    def formatter(self, content):
        content = content.splitlines()
        telemetry = {}
        for row in content:
            if not self.data_identifier.match(row):
                continue
            row = row.split("\t")
            vet = map(lambda a: float(a.replace(",", "")), row[2:-1])
            self.router.set_telemetry(vet)

            telemetry[row[0].lower()] = sum(self.router.to_list())  # get sum

        return telemetry


class PerCoreEmonMonitor(EmonMonitor):
    Cores = None

    def __init__(self, cmd, event_list=None, interval=1, cores=None):
        EmonMonitor.__init__(self, cmd, event_list, interval)

        if cores is not None:
            self.set_cores(cores)

    def set_cores(self, cores):
        self.Cores = map(int, cores.split(","))

    def formatter(self, content):
        content = content.splitlines()
        telemetry = {}
        for row in content:
            if not self.data_identifier.match(row):
                continue
            row = row.split("\t")
            # row = self.seprator.findall(row)
            vet = map(lambda a: float(a.replace(",", "")), row[2:-1])
            self.router.set_telemetry(vet)

            if self.Cores is None:
                telemetry[row[0].lower()] = sum(self.router.to_list())
            else:
                for core in self.Cores:
                    key = row[0].lower()
                    if key not in telemetry.keys():
                        telemetry[key] = 0
                    telemetry[key] += self.router[core]

        return telemetry


class GroupCoreEmonMonitor(EmonMonitor):
    Cores = None

    def __init__(self, cmd, event_list=None, interval=1, cores=None):
        EmonMonitor.__init__(self, cmd, event_list, interval)

        if cores is not None:
            self.set_cores(cores)

    def set_cores(self, cores):
        for i in cores:
            name = i
            if i.find("-"):
                start, end = tuple(i.split("-"))
                i = range(int(start), int(end) + 1)
            elif i.find(","):
                i = map(int, i.split)
            else:
                i = int(i)

            self.Cores.append((name, i))

    def formatter(self, content):
        content = content.splitlines()
        telemetry = {}
        for row in content:
            if not self.data_identifier.match(row):
                continue
            row = row.split("\t")
            # row = self.seprator.findall(row)
            vet = map(lambda a: float(a.replace(",", "")), row[2:-1])
            self.router.set_telemetry(vet)

            if self.Cores is None:
                telemetry[row[0].lower()] = sum(self.router.to_list())
            else:
                for name, core_group in self.Cores:
                    for core in core_group:
                        key = row[0].lower()
                        if key not in telemetry.keys():
                            telemetry[key] = {}
                            telemetry[key][name] = 0
                        telemetry[key][name] += self.router[core]

        return telemetry
