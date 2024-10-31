import math
import time


class PID():
    def __init__(self, p=10, i=0, d=0):
        self.p = p  # actually it's 100 since the error is percentage
        self.i = i
        self.d = d
        self.last_err = 0
        self.last_time = time.time()
        self.clear()

    def clear(self):
        self.last_err = 0
        self.last_time = time.time()

    def e2l(self, e):
        d_error = e - self.last_err
        d_t = time.time() - self.last_time
        X = self.p * e + self.i * e * d_t + self.d * d_error / d_t
        l = int(math.ceil(X)) #if X > 0 else int(math.floor(X))
        self.last_err = 0
        self.last_time = time.time()
        return l
