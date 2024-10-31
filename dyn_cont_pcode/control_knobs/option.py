from abc import ABCMeta, abstractmethod


class Option():
    __metaclass__ = ABCMeta

    def __init__(self, name, levels, level_index):
        self.name = name
        self.levels = levels
        self.level_index = level_index
        self.level_max = len(levels) - 1

    def get_name(self):
        return self.name

    def increase_level(self):
        if self.level_index < self.level_max:
            self.level_index += 1
            self.set_level()
            return True
        else:
            return False

    def decrease_level(self):
        if self.level_index > 0:
            self.level_index -= 1
            self.set_level()
            return True
        else:
            return False

    def reset_level(self):
        self.level_index = 0
        self.set_level()
        return True

    @abstractmethod
    def set_level(self):
        pass

    def get_level(self):
        return self.levels[self.level_index]

    def get_levels(self):
        return self.levels

    def get_level_index(self):
        return self.level_index

    def to_dic(self):
        return {"name": self.get_name(), "levels": self.get_levels(), "level": self.get_level(),
                "level_index": self.get_level_index()}
