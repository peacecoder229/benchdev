import logging
import os
import re
import sys
from itertools import islice
VERSION=0.1
logger = logging.getLogger('analyzer')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)-8s- %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Version : {}".format(VERSION))

class TraceAnalyzer(object):
    NUMBER_OF_LINES_TO_CHECK=1500
    MANDATORY_COUNTER="counter_0"

    def __init__(self, verbose):
        self.verbose=verbose
        self.platform = []

    def file_read_from_head(self, fname, nlines):
        result = ""
        try:
            with open(fname) as f:
                for line in islice(f, nlines):
                    result = result+line
        except Exception as e:
            pass
        return result

    def get_match(self, data, pat, key):
        matches = re.findall(pat, data)
        matching_value = None
        if matches:
            matching_value = matches[0][-1]
            matching_value = matching_value.strip()
            if key not in ["cpu_family", "hyper_threading"]:
                if matching_value.isdigit():
                    matching_value = int(matching_value)
        return matching_value

    def contains_emonversion_info(self, data):
        keys = {"emon_version" :  "EMON Version(.*)",
                "sep_driver_version": "SEP driver version:(.*)",
                "pax_driver_version": "PAX Driver Version:(.*)"}
        found_keys=[]
        for key, value in keys.items():
            matches = re.findall(value, data)
            if len(matches) > 0:
                found_keys.append(key)
        return len(found_keys) > 0

    def contains_emonm_info(self, data):
        pattern = "OS Processor <-> Physical/Logical Mapping"
        return pattern in data

    def get_platforminfo(self, data):
        keys = {"cpu_family": "cpu_family(.*)code named(.*)",
                "cpu_model": "cpu_model(\D*)(.*)\(",
                "cpu_stepping": "cpu_stepping(\D*)(.*)\(",
                "num_packages": "Number of Packages:(\D*)(.*)\)",
                "hyper_threading": "Hyper-Threading\)(.*)\((.*)\)",
                "cores_per_package": "Cores Per Package:(\D*)(.*)\)",
                "threads_per_package": "Threads Per Package:(\D*)(.*)\)",
                "threads_per_core": "Threads Per Core:(\D*)(.*)\)",
                "counter_0": "counter 0(.*) (.*)"}
        amd_cpu_family = "cpu_family(.*)AMD(.*)Processor"
        result = {}
        try:
            for key, pat in keys.items():
                result[key] = self.get_match(data, pat, key)
                if key == "cpu_family":
                    result['platform'] = result[key]
                    if result[key] == None:
                        result[key] = self.get_match(data, amd_cpu_family, key)
                        if result[key]: result['platform'] = 'AMD'
        except Exception as e:
            logger.error(e)
        return result

    def inst_ret_traces_exists(self, data, systeminfo, key):
        pat = systeminfo.get(key)
        if not pat: return False
        matches = re.findall(pat, data)
        if len(matches) >1:
            return True
        return False

    def analyze_dir(self, resultsPath, nested=False):
        emonV = []
        emonM = []
        emonD = []
        unfiedEmonD = []
        folderStructure = os.listdir(resultsPath)
        gplatforminfo = None
        for element in folderStructure:
            ch.terminator="\r"
            logger.info(".\r")
            ch.terminator="\n"
            sys.stdout.flush()
            target_file = os.path.join(resultsPath, element)
            if not os.path.isfile(target_file):
                continue
            if os.path.splitext(target_file)[-1] == ".xlsx":
                continue
            head_content = self.file_read_from_head(target_file, self.NUMBER_OF_LINES_TO_CHECK)
            platforminfo = self.get_platforminfo(head_content)
            if platforminfo.get("platform", None):
                gplatforminfo = platforminfo
        if not gplatforminfo:
            logger.info("Failed to find any complete emon trace file with emon platform/version info (i.e. emon.dat or emon.dat + emon-v.dat) in {}".format(resultsPath))
            return False
        for element in folderStructure:
            ch.terminator="\r"
            logger.info(".\r")
            ch.terminator="\n"
            sys.stdout.flush()
            target_file = os.path.join(resultsPath, element)
            if not os.path.isfile(target_file):
                continue
            if os.path.splitext(target_file)[-1] == ".xlsx":
                continue
            head_content = self.file_read_from_head(target_file, self.NUMBER_OF_LINES_TO_CHECK)
            platforminfo = self.get_platforminfo(head_content)
            if platforminfo: platforminfo = gplatforminfo
            version_info = self.contains_emonversion_info(head_content)
            plat = platforminfo.get("platform", None)
            if plat and plat not in self.platform: self.platform.append(plat)
            if "num_packages" in platforminfo and platforminfo['num_packages'] and  platforminfo['num_packages'] > 4:
                head_content = self.file_read_from_head(target_file, self.NUMBER_OF_LINES_TO_CHECK*2)
            valid_trace = self.inst_ret_traces_exists(head_content, platforminfo, self.MANDATORY_COUNTER)
            map_info=self.contains_emonm_info(head_content)     
            if version_info and valid_trace and map_info:
                unfiedEmonD.append(element)
            elif version_info and map_info:
                emonV.append(element)
            elif map_info and (not valid_trace) and (not version_info):
                emonM.append(element)
            elif valid_trace and (not map_info) and (not version_info):
                emonD.append(element)
            else:
                continue
        if not nested: print("")
        if len(unfiedEmonD) > 0:
            if self.verbose: logger.info("Successfully found unified emon file (emonv + emonm + emond) in {} processing further".format(resultsPath))
            return True
        elif len(emonV) > 0 and len(emonD) > 0 and len(emonM) > 0:
            if self.verbose: logger.info("Successfully found de-coupled emon traces (emonv, emonv, emond) in {} processing further".format(resultsPath))
            return True
        if self.verbose: logger.info("Failed to find any complete emon trace files (i.e. emon.dat) in {}".format(resultsPath))
        return False

    def analyze_nested_dirs(self, source):
        dirs=os.walk(source)
        directories=[x[0] for x in dirs]
        available_dirs = []
        missing=0
        self.platform = []
        logger.info("Analyzing nested dirs.. will take a while...")
        for directory in (directories[1:]):
            ch.terminator="\r"
            logger.info(".\r")
            ch.terminator="\n"
            sys.stdout.flush()
            if self.analyze_dir(directory, True):
                available_dirs.append(directory.split(source)[1].strip('/'))
            else:
                missing = missing + 1
        print("\n")
        return available_dirs, missing

if __name__ == "__main__":
    ta=TraceAnalyzer()
    ta.analyze_nested_dirs(sys.argv[1])
