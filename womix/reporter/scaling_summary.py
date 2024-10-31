#!/usr/bin/env python3

import os
import functools

from DataReader.base import RawDataFileReader
from DataReader.SPECjbb import SPECjbb2005Score
from DataReader.SPECcpu import SPECCPU2017Score, SPECCPU2006Score
import random

class WADReader(RawDataFileReader):
    def __init__(self, filename="widedeep.out"):
        self.filename = filename

    @property
    def TPS(self):
        raw = self.reader()
        line = raw[-1]
        line = line.split(":")
        return float(line[1])

class RN50Reader(RawDataFileReader):
    def __init__(self, filename="widedeep.out"):
        self.filename = filename

    @property
    def TPS(self):
        raw = list(self.grep("images per second"))

        line = raw[-1]
        line = line.split()
        return float(line[2])

class CluceneReader(RawDataFileReader):
    def __init__(self, filename="clucene.out"):
        self.filename = filename

        for i in self.grep_iterator(r"^QPS.*\d$"):
            self.data = i
        self.data = self.data.split(",")

    @property
    def qps(self):
        data = self.data[0].split()
        return float(data[1])

    @property
    def latency(self):
        data = self.data[1].split()
        return float(data[1])

def fake(path):
    return random.randint(0,1)    


def mlc(path):
    path = os.path.join(path, "mlc_out.txt")
    with open(path, "r") as fd:
        content = fd.readline()
    return float(content)

def specjbb(path):
    for i in os.listdir(path):
        if i.startswith("warhouse"):
            break
    path = os.path.join(path, i)
    # path = os.path.join(path, "summary.txt")
    reader = SPECjbb2005Score(path)
    return reader.throughput


def speccpu06(path, test, filename):
    path = os.path.join(path, filename)
    reader = SPECCPU2006Score(path, test)
    return reader.rate


def speccpu17(path, test):
    path = os.path.join(path, "CPU2017.001.fpspeed.refspeed.txt")
    reader = SPECCPU2017Score(path, test)
    return reader.rate


def clucene(path):
    path = os.path.join(path, "clucene.out")
    reader = CluceneReader(path)
    return reader.qps

def rn50(path):
    path = os.path.join(path, "rn50.out")
    reader = RN50Reader(path)
    return reader.TPS

def widedeep(path):
    path = os.path.join(path, "widedeep.out")
    reader = WADReader(path)
    return reader.TPS


MAP = {
    "specjbb": specjbb,
    "bwaves": functools.partial(speccpu06, test="bwaves", filename="CFP2006.001.ref.txt"),
    "libquantum": functools.partial(speccpu06, test="libquantum", filename="CINT2006.001.ref.txt"),
    #"bwaves": functools.partial(speccpu17, test="bwaves_s"),
    "rn50": rn50,
    "widedeep": widedeep,
    "perlbench": functools.partial(speccpu06, test="perlbench",
                                   filename="CINT2006.001.ref.txt"),
    "povray": functools.partial(speccpu06, test="povray",
                                filename="CFP2006.001.ref.txt"),
    "clucene": clucene,
    "memcached": lambda a: 100.0, # fake data
    "mlc": mlc, "mlc_benchmark": mlc,
    "fake": fake,
}

class PerformancePare:
    hp_score = 0
    lp_score = 0
    tag = "noname"

    def __init__(self, hp, lp, tag="noname"):
        self.hp_score = hp
        self.lp_score = lp
        
        self.tag = tag

    def __str__(self):
        return ("[%s, %s]" % (format(self.hp_score, '0,.1f'), format(self.lp_score, '0,.1f')))
        

def list_results(main_path):
    result = {}
    wl = os.path.basename(os.path.abspath(main_path))
    for folder in os.listdir(main_path):
        hp_folder = os.path.join(main_path, folder, "hp")
        try:
            hp_score = MAP[wl](hp_folder)
        except Exception as e:
            print ("%s at %s hp"% (e, hp_folder))
            hp_score = 0.0

        result[folder] = hp_score
    
    return result

if __name__ == "__main__":
    import sys
    root = sys.argv[1]

    data = list_results(root)
    for k, v in data.items():
        k = k.replace("_", " + ")
        print(k, v)


    

