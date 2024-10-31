#!/usr/bin/env python

import subprocess
import time
import optparse
import json
import os


class JobTask:
    """
    Base object to run shell commands
    """
    CMD = None
    process = None
    Kill = False

    def __init__(self, cmd):
        """
        :param cmd: Shell commands
        """
        self.CMD = cmd

    def start(self):
        """
        Execute command

        :return: None
        """
        self.process = subprocess.Popen(self.CMD, shell=True,
                                        stdout=subprocess.PIPE)

    def get_outputs(self):
        """
        Sync return outputs

        :return: iterator
        """
        while not self.Kill and self.process.returncode is None:
            row = self.process.stdout.readline().rstrip()
            value = self.format(row)
            if value is not None:
                yield value

    def format(self, row):
        """
        Format each of the output rows

        :param row: string
        :return: string
        """
        return row

    def __str__(self):
        return self.CMD


class TaskList:
    """
    Base object to run shell command list
    """
    Tasks = [
        ["echo \"Hello, Dolly\" > hello_dolly.txt"],
        ["echo \"Well, hello harry\" >> hello_dolly.txt"],
    ]

    def set_task_list(self, task_list):
        self.Tasks = task_list

    def append_task(self, task):
        self.Tasks.append(task)

    def __getitem__(self, item):
        """
        return Controller object for running

        :param item: int
        :return: Controller
        """
        offset = item % len(self.Tasks)
        return self.build(item, self.Tasks[offset])

    def build(self, uid, cmd):
        return Controller(uid, cmd)


class Controller(JobTask):
    """
    Controller of system configurations
    """

    # uuid
    UID = 0
    CMD = ""
    WorkPath = "./"

    def __init__(self, uid, cmd):
        """
        :param uid: int a uuid to distinguish the commands
        :param cmd: string
        """
        self.UID = uid
        self.WorkPath = "split_%s" % self.UID

        if isinstance(cmd, list):
            cmd = ";\n".join(cmd)

        os.mkdir(self.WorkPath)

        self.CMD = """
        #!/bin/bash
        
        ## include dependencies
        source ./test.src.sh
        WORK_PATH=`pwd`/%s
        mkdir -p $WORK_PATH
        
        ## main contents
        %s
        
         """ % (self.WorkPath, cmd)

        self.save_scripts()

    def save_scripts(self):
        script = os.path.join(self.WorkPath, "do_loop_%s.sh" % self.UID)
        with open(script, "w", ) as fd:
            fd.write(self.CMD)


class Framework:
    Job = None
    TaskList = None

    def __init__(self, job, task_list=None):
        self.Job = job
        if task_list is not None:
            self.TaskList = task_list
        else:
            self.TaskList = TaskList()

    def start(self):
        self.Job.start()
        for i, content in enumerate(self.Job.get_outputs()):
            yield content

            task = self.TaskList[i]
            task.start()


class SPECJbb2015OutputScore(JobTask):
    """
    SPECjbb2015 benchmark helper
    """
    Keyword = "TotalPurchase"
    StopLabel = "(quiescence.."

    Cycle = 0

    def format(self, row):
        if row.find(self.StopLabel) > 0:
            self.Kill = True
            self.process.terminate()

        if row.find("Ramping up completed") > 0:
            return "%0.4f: ramp up completed" % (time.time())

        if row.find(self.Keyword) > 0:
            self.Cycle += 1
            row = filter(lambda x: len(x) > 1, row.split(" "))
            return "%0.4f: Score, %s, %s" % (
                time.time(), self.Cycle, " ".join(row[7:]))

        return None


class JsonTaskList(TaskList):
    def __init__(self, conf):
        with open(conf, "r") as fd:
            self.set_task_list(json.load(fd))


FUNCTION_MAP = {
    "specjbb2015": SPECJbb2015OutputScore,
}


def main():

    parser = optparse.OptionParser()
    parser.add_option("-w", "--watch", dest="watch",
                      help="Watch outputs from command",
                      metavar="FILE")
    parser.add_option("-p", "--workload", dest="workload",
                      help="workload name",
                      metavar="FILE")
    parser.add_option("-f", "--queueu-file", dest="q",
                      help="A file contains task queue",
                      metavar="FILE")

    (options, args) = parser.parse_args()

    plugin = FUNCTION_MAP[options.workload.lower()]
    workload = plugin(options.watch)

    queue = JsonTaskList(options.q)
    fm = Framework(workload, queue)

    # fm = Framework(workload)
    for i in fm.start():
        print i


if __name__ == "__main__":
    main()
