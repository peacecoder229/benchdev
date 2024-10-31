from strategy import Strategy


class Priority(Strategy):
    def __init__(self, resource_list, target):
        name = "CPI_based_LLC_controller"
        super(Priority, self).__init__(name, resource_list, target)

    def decrease_level(self):
        for i in self.resource_list[::-1]:
            if i.decrease_level():
                return True
        return False

    def increase_level(self):
        for i in self.resource_list:
            if i.increase_level():
                return True
        return False

    def to_dic(self):
        resource_dic = {}
        for o in self.resource_list:
            resource_dic.setdefault(o.get_name(), o.to_dic())
        return {"name": self.name, "resources": resource_dic, "cpi_target": self.target}

    def set_config(self, resource_list, target):
        self.resource_list = resource_list
        self.target = target
