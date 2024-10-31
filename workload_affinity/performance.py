import os

class clucene_performance_monitor():

    def __init__(self, result_path="/pnpdata/clucene_benchmark_new/src/benchmark-dev/"):
        self.result_path = result_path

    def return_performance(self):
        try:
            input_file = self.result_path + 'log_*.log'
            output = os.popen('for i in `ls %s`; do tail -n 10000 $i |grep \'Search took\'|tail -n 1; done' % input_file)
            result = output.read()
            if result == '':
                return -1
            l = result.strip().split('\n')
            fltl = [float(i.split(':')[1]) for i in l]
            c = sum(fltl)
            c = sum(fltl)/len(fltl)
            return c
        except:
            return -1

