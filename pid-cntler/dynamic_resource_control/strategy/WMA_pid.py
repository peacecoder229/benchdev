import math
import time


class WMAPID():
    def __init__(self, p=10, i=0, d=0, window_length=3, window_weight=[0.1, 0.2, 0.7]):
        self.p = p  # actually it's 100 since the error is percentage
        self.i = i
        self.d = d
        self.last_err = 0
        self.last_time = time.time()
        self.clear()
        self.data=[]
        self.window_length = window_length
        self.window_weight = window_weight

    def clear(self):
        self.last_err = 0
        self.last_time = time.time()
        self.data = []

    def e2l(self, error):
        e = self.ma(error)
        d_error = e - self.last_err
        d_t = time.time() - self.last_time
        X = self.p * e + self.i * e * d_t + self.d * d_error / d_t
        l = int(math.ceil(X)) #if X > 0 else int(math.floor(X))
        self.last_err = 0
        self.last_time = time.time()
        return l

    def ma(self, input):
        self.data.append(input)
        while len(self.data)>self.window_length:
            self.data.pop(0)
        if len(self.data) < self.window_length:
            return sum(self.data)/len(self.data)
        else:
            result = 0
            for i in range(self.window_length):
                result += self.data[i]*self.window_weight[i]
            return result
            
        
