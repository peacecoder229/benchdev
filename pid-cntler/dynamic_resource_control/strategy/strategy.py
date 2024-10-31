from abc import ABCMeta, abstractmethod

class Strategy():
    __metaclass__ = ABCMeta

    def __init__(self, name, resource_list):
        self.name = name
        self.resource_list = resource_list

    @abstractmethod
    def increase_level(self):
        pass

    @abstractmethod
    def decrease_level(self):
        pass
