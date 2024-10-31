import numpy as np

class WorkloadType():
    def __init__(self):
        self.T = []
        self.X = []
        self.Y = []
        self.D = []
        self.f = []

    def get_fit(self):
        self.f = np.polyfit(self.X, self.Y, 1)
        return self.f

    def get_D(self):
        if (len(self.X)<2) or (len(self.X) != len(self.Y)):
            return 0
        for i in range(len(self.X) - 1):
            if (self.X[i + 1] - self.X[i]) == 0:
                self.D.append(0)
            else:
                self.D.append((self.Y[i + 1] - self.Y[i]) / (self.X[i + 1] - self.X[i]))
        return 1

    def get_linearity(self):
        e = 0
        y = 0
        for i in range(len(self.X)):
            error_i = self.X[i] * self.f[0] + self.f[1] - self.Y[i]
            e = error_i if abs(error_i)>e else e
            y = self.Y[i] if abs(self.Y[i]) > y else y

        if y == 0:
            return 0
        else:
            return float(e)/float(y)

    def feed_data(self, input_x, input_y):
        self.T.append((float(input_x), float(input_y)))
        self.X.append(float(input_x))
        self.Y.append(float(input_y))

    def get_result(self):
        self.get_fit()
        self.get_D()
        return self.f, self.get_linearity()

    def resort(self):
        self.T = sorted(self.T, key=lambda t: t[0])
        self.X = [i[0] for i in self.T]
        self.Y = [i[1] for i in self.T]
        return 1

    def find_flat(self):
        start = 0
        j = 0
        result = []
        while 1:
            if abs(self.D[start+j]) < abs(self.f[0]/10):
                j += 1
            else:
                if j == 0:
                    start += 1
                else:
                    result.append((self.X[start], self.X[start+j]))
                    start = start + j +1
                    j = 0
            if start + j >= len(self.D):
                if j > 0:
                    result.append((self.X[start], self.X[start + j]))
                    break
                else:
                    break
        return result


if __name__ == "__main__":
    W = WorkloadType()
    P = [284419.84,98864.55,216547.96,125849.63,109389.34,106485.92]
    MBA = [10,100,20,30,40,50]
    MBM = [10687.4,6751.7,8953,8408.3,8016.8,7419.1]

    testA = [1,2,3,4,5,6]
    testB = [10,30,50,70,70,70]
    #P = [4600,7200,4800,5700,7000,6900,5000,6000,6600,17000,21000,4600,6600,4700,5300,6500,6500,4500,6800,4700,5300,6300,6500,4500,6800,4700,5400,6400,6600,3800,5600,3800,4100,5000,5200,3800,5600,3900,4100,5000,5100,3700,5100,3700,3900,4600,4900,3700,5200,3700,3900,4700,4800,3700,5200,3800,4000,4700,4900]
    #MB = [3120.451314,3025.008082,3381.101662,3353.320292,3004.915173,3231.010348,2533.731138,2549.025888,2528.214512,2449.002441,2532.411988,2641.104455,2642.17276,2646.215244,2643.550062,2592.059597,2592.952985,2780.126819,2657.66069,2669.179412,2693.573403,2697.670409,2616.684523,2778.95697,2690.693914,2774.575524,2797.215642,2777.881132,2773.38101,3026.136792,3071.209989,3158.043218,3252.630079,3487.220925,3281.254839,2475.309233,2433.726496,2512.472793,2431.38438,2642.275525,2495.499574,2596.765127,2642.145822,2694.068504,2787.503101,2681.955193,2649.739797,2651.804938,2696.627038,2760.669492,2594.598925,2882.750073,2663.776266,2801.59184,2709.170028,2833.48916,2715.530213,2700.329549,2693.791543]
    for i in range(len(P)):
        #W.feed_data(MBM[i], P[i])
        W.feed_data(testA[i], testB[i])
    print W.resort()
    print W.get_result()
    print W.find_flat()
    plt.plot(W.X, W.Y)
    plt.show()

