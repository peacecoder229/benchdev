import os
from option import Option
import logging


class MBA(Option):
    def __init__(self, level_index, COS, cores):
        name = "MBA"
        levels = ['100', '70', '50', '40', '30', '20', '10']
        super(MBA, self).__init__(name, levels, level_index)
        self.COS = COS
        self.cores = cores

    def set_level(self):
        os.system('pqos -a LLC:%s=%s > /dev/null' % (self.COS, self.cores))
        os.system('pqos -e MBA:%s=%s > /dev/null' % (self.COS, self.levels[self.level_index]))
        CL = logging.getLogger('closeloop')
        CL.info("%s Resource reallocated, COS%s, %s:%s" % (self.name, self.COS, self.name, self.get_level()))

    def set_config(self, COS, cores):
        self.COS = COS
        self.cores = cores
        self.set_level()


if __name__ == "__main__":
    M = MBA(0, 4, "0-3")
    print M.get_level()
