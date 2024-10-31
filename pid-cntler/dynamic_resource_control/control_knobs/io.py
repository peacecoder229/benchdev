import os
from option import Option
import logging


class IO(Option):
    def __init__(self, level_index, COS, cores, device):
        name = "IO"
        levels = []
        super(IO, self).__init__(name, levels, level_index)
        levels = []
        self.COS = COS
        self.cores = cores
        self.device = device
        self.path = '/sys/fs/cgroup/blkio/%s' % COS
        os.system('mkdir - p %s' %self.path)


    def set_level(self):
        os.system('echo \'%s   %s\' > %s/blkio.throttle.read_bps_device' %(self.device, self.get_level(), self.path))
        os.system('echo \'%s\' > %s/tasks' % (self.get_level(), self.path))
        pass

    def set_config(self, COS, cores):
        self.COS = COS
        self.cores = cores
        self.set_level()


if __name__ == "__main__":
    pass