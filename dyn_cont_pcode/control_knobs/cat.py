import os
from option import Option
import logging


class CAT(Option):
    def __init__(self, level_index, COS, cores):
        name = "CAT"
        levels = []
        #for i in range(10):
        for i in range(0,10,2):
            levels.append(hex(0x7ff >> i))
        super(CAT, self).__init__(name, levels, level_index)
        self.COS = COS
        self.cores = cores

    def set_level(self):
        os.system('pqos -a LLC:%s=%s > /dev/null' % (self.COS, self.cores))
        os.system('pqos -e LLC:%s=%s > /dev/null' % (self.COS, self.levels[self.level_index]))
        CL = logging.getLogger('closeloop')
        CL.info("%s Resource reallocated, COS%s, %s:%s" % (self.name, self.COS, self.name, self.get_level()))

    def set_config(self, COS, cores):
        self.COS = COS
        self.cores = cores
        self.set_level()


if __name__ == "__main__":
    C = CAT(0, 4, "0-3")
    print C.get_level()
