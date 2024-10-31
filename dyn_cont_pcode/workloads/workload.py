from abc import ABCMeta, abstractmethod

class Workload():
    __metaclass__ = ABCMeta

    def __init__(self, name, PID, cores, COS, resource_list, weight=100):
        self.name = name
        self.PID = PID
        self.cores = cores
        self.COS = COS
        self.resource_list = resource_list
        self.weight=weight

#    @abstractmethod
    def start_workload(self):
        pass

#    @abstractmethod
    def stop_workload(self):
        pass

    def SLA_function(self):
        pass

    def set_sla(self, function):
        self.SLA_function = function

    def get_sla(self):
        return self.SLA_function()

    def set_COS(self, COS):
        self.COS = COS

    def set_cores(self, cores):
        self.cores = cores

    def set_weight(self, weight):
        self.set_weight=weight

    def get_weight(self):
        return self.weight

    def get_COS(self):
        return self.COS

    def get_cores(self):
        return self.cores

    def get_info(self):
        return {"name":self.name, "PID":self.PID}

if __name__ == "__main__":

    def test_sla():
        return "this is a test sla"
    D = Workload("test", 0, "0-13", "4", [], 50)
    print D.get_sla()