import pickle
import os
import numpy as np

class Detector:
    def __init__(self):
        self.min_max_scaler = None
        self.clf = None

    def load_model(self, scaler='MinMaxScaler.pkl', clf='MLP.pkl'):
        with open(scaler) as scaler_file:
            self.min_max_scaler = pickle.load(scaler_file)
        with open(clf) as clf_file:
            self.clf = pickle.load(clf_file)

    def detect(self, metrics):
        if self.min_max_scaler and self.clf:
            metrics_s = self.min_max_scaler.transform(metrics)
            return self.clf.predict(metrics_s)
        else:
            print "Please load model first!"
            return None

    def read_metrics(self):
        output = os.popen('./skx_metrics')
        datalist = output.read().split(',')[:3]
        output = np.array(datalist, ).astype('float64')
        output = output[:, None]
        output = output.transpose()
        return output

    def output_result(self):
        return self.detect(self.read_metrics())

if __name__ == "__main__":
    D = Detector()
    D.load_model()
    output = os.popen('./skx_metrics')
    datalist = output.read().split(',')[:3]
    output = np.array(datalist, ).astype('float64')
    output = output[:, None]
    output = output.transpose()

    print D.detect(output)
