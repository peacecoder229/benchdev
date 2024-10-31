import os
from option import Option
import logging


class CoreNumbers(Option):
    def __init__(self, level_index, COS, cores):
        name = "CoreNumbers"
        levels = []
        super(CoreNumbers, self).__init__(name, levels, level_index)
        levels = []
        self.COS = COS
        self.cores = cores

    def set_level(self):
        pass

    def set_config(self, COS, cores):
        self.COS = COS
        self.cores = cores
        self.set_level()


if __name__ == "__main__":
    pass