import math

class IPCChecker():
    def __init__(self, p = 0.9, s_window_length=3, l_window_length=5):
        self.s_window=[]
        self.l_window=[]
        self.s_window_length = s_window_length
        self.l_window_length = l_window_length
        self.p = p

    def clear(self):
        self.s_window_length = [] 
        self.l_window_length = [] 

    def check(self, input):
        self.s_window.append(input)
        self.l_window.append(input)
        while len(self.s_window)>self.s_window_length:
            self.s_window.pop(0)
        while len(self.l_window)>self.l_window_length:
            self.l_window.pop(0)
        s_avg = sum(self.s_window)/len(self.s_window)
        l_avg = sum(self.l_window)/len(self.l_window)
        return (s_avg > l_avg * self.p)
