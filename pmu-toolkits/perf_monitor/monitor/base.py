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

import subprocess
import random
import time

THREAD = 0x00
PROCESS = 0x10

TASK_LEVEL = THREAD

if TASK_LEVEL is THREAD:
    # multiple thread mode
    from threading import Thread
    from Queue import Queue

if TASK_LEVEL is PROCESS:
    # multiple process mode
    from multiprocessing import Process as Thread
    from multiprocessing import Queue


class MonitorError(Exception):
    pass


class MonitorBase:
    """
    Base monitor launcher
    """
    Name = "unset"

    WorkloadInstance = None
    default_workload = "sleep 3600"
    EventList = []
    Inteval = 1

    # Save monitor raw data to a list
    KeepMonitorRawData = False
    MonitorRawData = []

    # fake monitor
    monitor_command = "sleep 1"

    def __init__(self, cmd, event_list=None, interval=1):
        """
        initialize
        :param cmd: str | launch workload for calibrations
        :param event_list: list | events need counting
        :param cores: cores
        :param interval: int | time inteval
        """
        self.default_workload = cmd

        if event_list is not None:
            self.set_event_list(event_list, interval)

    def set_name(self, name):
        """
        Set a label for monitor

        :param name: str
        :return:
        """
        self.Name = name

    def set_event_list(self, event_list, inteval=1):
        self.EventList = event_list
        self.Inteval = inteval

    def start_workload(self, output_file=None):
        """
        Async start workload

        :param output_file: redirect out put to a file
        :return:
        """
        if output_file is None:
            output_file = subprocess.PIPE
        else:
            output_file = open(output_file, "a")
        workload = subprocess.Popen(self.default_workload,
                                    stdout=output_file,
                                    shell=True)
        if workload.returncode is not None:
            raise MonitorError(
                "Workload exec error: %s " % self.default_workload)
        else:
            self.WorkloadInstance = workload

    def get_output(self):
        return self.WorkloadInstance.stdout

    def set_monitor_command(self):
        pass

    def start_monitor(self):
        """
        Start monitor main loop

        :return: iterator, telemetries
        """

        if self.WorkloadInstance is None:
            raise MonitorError("Workload haven't been started!")

        while True:
            self.set_monitor_command()
            if self.WorkloadInstance.poll() is not None:
                # stop monitor when workload stopped
                break
            else:
                # start monitor and get results

                content = subprocess.check_output(self.monitor_command,
                                                  shell=True)
                if self.KeepMonitorRawData:
                    self.MonitorRawData.append(
                        "Exec: %s" % self.monitor_command)
                    self.MonitorRawData.append("Result: \n%s" % content)

                yield self.formatter(content)

    def formatter(self, content):
        """
        An interface class to covert raw data returned from monitor
        :param content: str
        :return: mix
        """
        return content

    def __and__(self, other):
        """
        Enable user to parallel 2 monitors by monitor1 &= monitor2

        :param other:
        :return: MonitorTaskManager
        """

        task_manager = MonitoringTaskManager()
        task_manager.set_monitor(self)

        other.WorkloadInstance = self.WorkloadInstance
        task_manager.set_monitor(other)

        return task_manager


class MonitoringTask(Thread):
    """
    Package a monitor instance, in order to start it in multiple threads
    """
    Monitor = None
    Q = None

    def set_monitor(self, monitor):
        """
        Set monitors

        :param name: monitor's idx
        :param monitor: monitor instance
        :return: None
        """
        self.Monitor = monitor

    def start_workload(self, output=None):
        self.Monitor.start_workload(output_file=output)

    def set_queue(self, queue):
        """
        Set a queue for communication.

        :param queue: queue instance
        :return: None
        """
        self.Q = queue

    def run(self):
        """
        over ride parent method for start monitor

        :return: None
        """
        for current_value in self.Monitor.start_monitor():
            message = (self.Monitor.Name, time.time(), current_value)
            self.Q.put(message)


class MonitoringTaskManager(MonitorBase):
    """
    Task manager for multiple monitors
    """
    Q = None
    Pool = {}

    def __init__(self, interval=1):
        """
        initial Q

        :param interval: float timeout for Q
        """

        self.Q = Queue()
        self.Interval = interval

    def set_monitor(self, monitor):
        """
        Add monitor tasks to the framework

        :param name: str, set a label for monitor
        :param monitor: Monitor instance
        :return: None
        """
        task = MonitoringTask()
        task.set_monitor(monitor)
        task.set_queue(self.Q)

        self.Pool[monitor.Name] = task

    def start_workload(self):
        """
        start workloads parallel

        :param output_file: filename
        :return: None
        """
        for task in self.Pool.values():
            task.start_workload(output_file=None)

    def start_monitor(self):
        """
        Read monitor telemetries form queue

        :return: iterator
        """
        for task in self.Pool.values():
            task.start()

        while True:
            if self.Q.empty():
                for name, task in self.Pool.items():
                    if not task.is_alive():
                        del (self.Pool[name])

                if len(self.Pool) is 0:
                    break
            else:
                yield self.formatter(self.Q.get(timeout=self.Interval))

    start_monitors = start_monitor  # set alias here

    def formatter(self, content):
        name, timestamp, current_value = content
        current_value["timestamp"] = timestamp
        current_value["monitor"] = name

        return current_value

    def __and__(self, other):
        if isinstance(other, MonitoringTaskManager):
            raise MonitorError("instance %s cannot be attached! ")
        if not isinstance(other, MonitorBase):
            raise MonitorError("instance %s is not a child of MonitorBase")

        self.set_monitor(other)

        return self


class FakeMonitor(MonitorBase):
    """
    Fake monitor for debug
    """

    def __init__(self, cmd, event_list=None, interval=1, *args, **kwargs):
        MonitorBase.__init__(self, cmd, event_list, interval)

    def start_monitor(self):
        for _ in xrange(0xff):
            yield self.formatter(1)
            time.sleep(self.Inteval)

    def formatter(self, content):
        fake_data = {k.lower(): random.randint(1, 1024) for k in
                     self.EventList}
        return fake_data
