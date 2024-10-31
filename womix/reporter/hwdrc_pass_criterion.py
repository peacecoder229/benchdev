#!/usr/bin/env python3

import os
import functools

from DataReader.base import RawDataFileReader
from DataReader.SPECjbb import SPECjbb2005Score
from DataReader.SPECcpu import SPECCPU2017Score, SPECCPU2006Score
from DataReader.redis import MemtierJsonReader
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

def memcached(path):
    path = os.path.join(path, "result.json")
    reader = MemtierJsonReader(path)
    return reader.ops


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
    "memcachedserver": memcached,
    "mlc": mlc, "mlc_benchmark": mlc,
    "fake": fake,
}


class Score:
    
    def __init__(self, hp, lp, tag="no-name"):
        self.hp = hp
        self.lp = lp
        self.tag= tag
    
    def __str__(self):
        fmt = lambda a: format(a, '0,.1f')

        return "%s {hp: %s, lp: %s}" %(self.tag, fmt(self.hp), fmt(self.lp))

    def __eq__(self, other):
        return (self.hp * VARATION[1]) >= (other.hp*VARATION[0]) and (other.hp * VARATION[1]) >= (self.hp*VARATION[0])
    
    def __gt__(self, other):
        return self.hp * VARATION[0] >= other.hp 

    
    def __lt__(self, other):
        return self.hp * VARATION[0] <= other.hp

class PerformancePare:
    def __init__(self, main_path):
        self.path = main_path
        basename = os.path.basename(main_path)
        self.hp, self.lp = tuple(basename.split("-"))
    
    def __str__(self):
        return "%s + %s" % (self.hp, self.lp)

    def scores(self, sub_case):
        path = os.path.join(self.path, sub_case)
        hp_folder = os.path.join(path, "hp")
        lp_folder = os.path.join(path, "lp")
        try:
            hp_score = MAP[self.hp](hp_folder)
        except:
            hp_score = 0

        try:
            lp_score = MAP[self.lp](lp_folder)
        except:
            lp_score = 0

        return Score(hp_score, lp_score, "%s + %s @%s" % (self.hp, self.lp, sub_case))

    @property
    def BASE(self):
        return self.scores("00_non")
    
    @property
    def HWDRC(self):
        return self.scores("03_hwdrc")
    
    def mba_scores(self, mba):
        path = "01_rdt_MBA%s" % mba
        return self.scores(path)

    @property
    def MAX_MBA(self):
        return self.mba_scores(10)

    @property
    def OPT_MBA(self):
        best = None
        for mba in range(10, 100, 10):
            mba = self.mba_scores(mba)
            if best is None or mba.hp >= self.MAX_MBA.hp * SLO:
                best = mba
        return best

def list_results(main_path):
    result = {}
    for folder in os.listdir(main_path):
        path = os.path.join(main_path, folder)
        wl_pare = PerformancePare(path)

        print("%s: %s" % (wl_pare, wl_pare.HWDRC == wl_pare.OPT_MBA))

        print(wl_pare.BASE)
        print(wl_pare.HWDRC)
        print(wl_pare.OPT_MBA)

    

VARATION=(0.95, 1.05)
SLO = 0.9

if __name__ == "__main__":
    import sys
    root = sys.argv[1]
    list_results(root)
