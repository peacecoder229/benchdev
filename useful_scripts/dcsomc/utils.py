import os
import sys
import importlib
import datetime
import subprocess
import time
from argparse import Namespace
import logging
VERSION=0.1

logger = logging.getLogger('utils')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)-8s- %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Version : {}".format(VERSION))

REQUIRED_TOOLS = ['psutil', 'pgrep', 'easysettings']

def install(package):
    import pip as p
    # TODO: Fix this ugly work around to mitigate PIP issue.
    if int(p.__version__.split('.')[0]) > 9:
        from pip._internal import main as pip_main
        pip_main(['install', package])
    else:
        if hasattr(p, 'main'):
            p.main(['install', package])

def check_install_tools(PACKAGE_LIST=REQUIRED_TOOLS):
    package=""
    try:
        for p in PACKAGE_LIST:
            package = p
            importlib.import_module(package)
        logger.info("Required modules are available...!")            
    except ImportError:
        logger.error("{} not found, trying to install and fix it".format(package))
        sys.exit(1)
    return True


def generate_dir_with_ts(append=None):
    datets = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if append: return "{}_{}".format(append, datets)
    return "sample_{}".format(datets)

def get_unique_dir(opath):
    root_dir=os.path.normpath(opath)
    dirname=os.path.basename(root_dir)
    root_dir=os.path.dirname(root_dir)
    counter = 1
    while os.path.exists(opath):
        opath = os.path.join(root_dir, "{}_{}".format(dirname,counter))
        counter = counter + 1
    return opath

def run_command(command, timeout=5):
    iniTime = time.time()
    pemonv = subprocess.Popen(command, shell=True, executable='/bin/bash')
    while pemonv.poll() is None:
        time.sleep(0.1)
        endTime = time.time()
        if endTime - iniTime >= 5:
            logger.error("Waited for 5 seconds and failed to complete emon-v data collection process, killing {} ".format(pemonv.pid))
            pemonv.kill()
