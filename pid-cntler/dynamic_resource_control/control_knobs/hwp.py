import os
from option import Option
import logging


class HWP(Option):
    def __init__(self, level_index, COS, cores):
        name = "HWP"
        levels = range(32, 33, 1)
        super(HWP, self).__init__(name, levels, level_index)
        self.COS = COS
        self.cores = cores
        self.set_level()

    def set_level(self):
        os.system('x86_energy_perf_policy --cpu %s --hwp-desired %s > /dev/null' % (self.cores, self.get_level()))
        #CL = logging.getLogger('closeloop')
        #CL.info("%s Resource set, %s:%s" % (self.name, self.name, self.get_level()))

    def set_config(self, COS, cores):
        self.COS = COS
        self.cores = cores
        self.set_level()


if __name__ == "__main__":
    C = HWP(0, 4, "0-3")
    print C.get_levels()
