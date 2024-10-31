import math

class IPCChecker():
    def __init__(self, p = 0.9):
        self.history_ipc_max = 0
        self.p = p

    def check(self, input):
        if input > self.history_ipc_max:
            self.history_ipc_max = input
        return (input > self.history_ipc_max * self.p)
