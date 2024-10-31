import os
import time

WORKLOAD_NUM = 0
WORKLOAD_MAX = 20
workload_waiting = lambda: WORKLOAD_NUM < WORKLOAD_MAX


def register(name, pid, type='BE'):
    # TODO http service
    if type == 'BE':
        pass
    elif type == 'PR':
        pass


def stop_workload(pid):
    cmd = "docker rm -f %s 2>&1" % pid
    p = os.popen(cmd)
    result = p.readlines()[0]
    return result


def start_stream(cores):
    docker_name = "stream" + str(time.time())
    cmd = "docker run --cpuset-cpus=%s -d --name %s stream 2>&1" % (
    cores, docker_name)
    p = os.popen(cmd)
    pid = p.readlines()[0]
    return (docker_name, pid)


class Cmd2Action():
    def __init__(self, cmd):
        self.cmd = cmd

    def action(self):
        request = {
            # "/" : self.__load_index(),
            "/get_workload_waiting": self.get_workload_waiting,
            "/stop_workload": self.stop_workload,
            "/apply_for_workload": self.apply_for_workload
        }
        return request[self.cmd.split("?")[0]]()

    def get_workload_waiting(self):
        return workload_waiting()

    def stop_workload(self):
        pid = self.cmd.split("?")[1]
        try:
            # result = os.kill(pid)
            result = stop_workload(pid)
            return result

        except OSError as e:
            return e

    def apply_for_workload(self):
        if self.get_workload_waiting():
            cores = self.cmd.split("?")[1]
            name, pid = start_stream(cores)
            register(name, pid)
            return True
        else:
            return False
