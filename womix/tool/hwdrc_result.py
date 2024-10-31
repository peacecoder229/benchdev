import os
import functools

from DataReader.base import RawDataFileReader
from DataReader.SPECjbb import SPECjbb2005Score
from DataReader.SPECcpu import SPECCPU2017Score, SPECCPU2006Score


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


def specjbb(path):
    path = os.path.join(path, "warhouse24.out")
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
    "bwaves": functools.partial(speccpu17, test="bwaves_s"),
    "rn50": rn50,
    "widedeep": widedeep,
    "perlbench": functools.partial(speccpu06, test="perlbench",
                                   filename="CINT2006.001.ref.txt"),
    "povray": functools.partial(speccpu06, test="povray",
                                filename="CFP2006.001.ref.txt"),
    "clucene": clucene
}


def main(main_path):
    for folder in os.listdir(main_path):
        # if not os.path.isdir(folder):
        #     continue
        hp, lp = tuple(folder.split("-"))
        try:
            hp_score = MAP[hp](os.path.join(main_path, folder, "hp"))
        except:
            print(os.path.join(main_path, folder, "hp"))
            hp_score = "unknown"
        try:
            lp_score = MAP[lp](os.path.join(main_path, folder, "lp"))
        except:
            print(os.path.join(main_path, folder, "lp"))
            lp_score = "unknown"

        print("%s: %s, %s" % (folder, hp_score, lp_score))


if __name__ == "__main__":
    import sys

    main_path = sys.argv[1]
    main(main_path)
