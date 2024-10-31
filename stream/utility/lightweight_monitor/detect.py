import os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.externals import joblib

clf = joblib.load('km.pkl')

with open('max.txt') as file:
    line = file.readline()
    max_list = line.split(',')

max = np.array(max_list).astype('float64')

while 1:
    output = os.popen('./skx_metrics')
    datalist = output.read().split(',')[:3]
    print datalist
    test = np.array(datalist,).astype('float64')
    output = test/max
    #print output
    output = output[:,None]
    output =  output.transpose()

    print clf.predict(output)
