#!/usr/bin/env python

import argparse
import datetime
import errno
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
from argparse import Namespace
import multiprocessing

os.environ["PYTHONUNBUFFERED"] = "1"

from utils import check_install_tools, generate_dir_with_ts, get_unique_dir
from dcsomc import PlatformUtil, PostProcessor
import metadata
import psutil as psu
import pgrep 

VERSION=0.1
system_tools_available = check_install_tools()

logger = logging.getLogger('tmc')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)-8s- %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Version : {}".format(VERSION))


COLLECTORS_CONFIG = {
    "emon" : {'collector_type': 'emon', 'binary' : 'emon', 'arguments' : '', 'samplingrate' : ''},
    "sar" : {'collector_type': 'sar', 'binary' : 'sar', 'arguments' : '-A', 'samplingrate' : '1', 'postprocess' : 'sadf -t -d {} -- -A > {}'},
    "iostat" : { 'collector_type': 'redirect', 'binary' : 'iostat', 'arguments' : '-kxt', 'samplingrate' : '1'},
    "vmstat" : {'collector_type': 'redirect','binary' : 'vmstat', 'arguments' : '-tn', 'samplingrate' : '1'},
}

default_args = Namespace(dir="", time_stamp="", emonPath="/opt/intel/sep")
class ProcessHandler(object):
    pargs = None

    def __init__(self, commandlineargs):
        self.pargs = commandlineargs

    def get_process_summary(self, pobj):
        res = ""
        pargs = pobj.cmdline()
        if pargs:
            res += "Target process command :\n"
            res += " ".join(pargs)
            res += "\n"
        return res

    def kill_target(self, pid):
        import signal
        os.killpg(os.getpgid(pid), signal.SIGTERM)

    def wait_for_target(self, pargs):
        pobj = psu.Process(int(pargs.process_id))
        pid_check = "psu.pid_exists({})".format(pargs.process_id)
        process_summary = self.get_process_summary(pobj)
        if pargs.verbose:
            logger.info(process_summary)
        if pargs.max_timeout:
            _timeout = time.time() + pargs.max_timeout
        try:
            while eval(pid_check) and pobj.status() != psu.STATUS_ZOMBIE:
                if pargs.max_timeout and (time.time() > _timeout):
                    self.kill_target(pargs.process_id)
                    break
                time.sleep(1)
        except psu.NoSuchProcess as e:
            logger.error(e)
            pass
        except Exception as e:
            logger.error(e)

    def run_command(self, commands, logfilehandle=None, silent=False):
        try:
            p = subprocess.Popen(self.pargs.target_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid, executable='/bin/bash')

            def stdreader():
                while True:
                    line = p.stdout.readline()
                    if not line:
                        break
                    if logfilehandle and not logfilehandle.closed:
                        logfilehandle.write(line.decode(sys.stdout.encoding))
                    if not silent:
                        logger.info(line.decode(sys.stdout.encoding).strip("\n"))
                    logfilehandle.flush()

            def errreader():
                while True:
                    line = p.stderr.readline()
                    if not line:
                        break
                    if logfilehandle and not logfilehandle.closed:
                        logfilehandle.write(line.decode(sys.stdout.encoding))
                    if not silent:
                        logger.info(line.decode(sys.stdout.encoding).strip("\n"))
                    logfilehandle.flush()

            t1 = threading.Thread(target=errreader)
            t1.start()
            t2 = threading.Thread(target=stdreader)
            t2.start()
            return p.pid
        except Exception as e:
            print(e)
            return None

    def start_target(self, pargs, logfile):
        try:
            process_id = self.run_command(pargs.target_cmd, logfilehandle=logfile)
            time.sleep(1)
            pobj = psu.Process(int(process_id))
            if psu.pid_exists(process_id) and pobj.status() != psu.STATUS_ZOMBIE:
                return process_id
        except Exception as ex:
            logger.error("Error while starting the given target command")
            logger.error(str(ex))
        return None


class BaseCollector(object):
    disable_sampling = True
    verbose = False
    setup_ready = False
    samping_thread = None
    config = None
    affinitize_core = None
    results = os.getcwd()

    def __init__(self, destdir, tool_name, args=None):
        if hasattr(args, 'verbose') and args.verbose:
            self.verbose = args.verbose
        self.results = destdir
        self.toolname = tool_name
        self.affinitize_core = args.affinitize_core

        try:
            os.makedirs(self.results)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def prepare_sampling(self):
        logger.info("Steps to prepare samping!")
        return True

    def start_sampling(self):
        logger.info("Start samping process...!")

    def stop_sampling(self):
        self.disable_sampling = True

    def get_data_path(self):
        return self.results

    def start(self):
        try:
            if self.prepare_sampling():
                self.samping_thread = threading.Thread(target=self.start_sampling)
                self.samping_thread.daemon = True
                self.samping_thread.start()
            else:
                logger.error("Failed to prepare the setup for {} data collection...".format(self.toolname))
        except KeyboardInterrupt:
            logger.info('Received KeyboardInterrupt, shutting down the {} collector'.format(self.toolname))
            self.disable_sampling = True

    def stop(self, closehandles=None):
        self.disable_sampling = True
        if self.samping_thread:
            logger.info("Stopping {} collector process, joining background thread".format(self.toolname))
            self.samping_thread.join()
        if closehandles:
            closehandles.close()

    def is_already_inuse(self):
        return len(pgrep.pgrep(' -x {} '.format(self.toolname)))

    def is_running(self):
        if self.samping_thread:
            return self.samping_thread.is_alive()
        else:
            return False

    def wait_forever(self):
        logger.info("{} collector will be running until user kills (ctrl+c).".format(self.toolname))
        while True:
            time.sleep(1)
            if not self.is_running():
                break


class EmonCollector(BaseCollector):
    emonPath = "/opt/intel/sep"
    input = None
    emonthread = None

    def __init__(self, *args, **kwargs):
        super(EmonCollector, self).__init__(*args, **kwargs)
        inputargs=kwargs.get('args')
        if hasattr(inputargs, 'binary_emon') and inputargs.binary_emon:
            self.emonPath = inputargs.binary_emon
        # Validating EMON path
        if not os.path.isfile(self.emonPath + "/sep_vars.sh"):
            logger.error("The EMON path provided is incorrect, exiting script")
            return
        if hasattr(inputargs, 'events_file') and inputargs.events_file:
            if os.path.isfile(os.path.join(os.getcwd(),inputargs.events_file)):
                self.input = os.path.join(os.getcwd(),inputargs.events_file)
            elif os.path.isfile(os.path.join(self.emonPath, inputargs.events_file)):
                self.input = os.path.join(self.emonPath, inputargs.events_file)
            else:
                self.input = None
            logger.info("Using user provided input events file located in {}".format(self.input))
        self.basecmd = "source " + self.emonPath + "/sep_vars.sh" + " &> /dev/null "
        self.setup_ready = True

    def reload_emon(self):
        try:
            scripts_path=os.path.dirname(sys.argv[0])
            reload_script=os.path.join(scripts_path,"remon")
            reload_sep_output = __import__('subprocess').check_output('bash {}'.format(reload_script), shell=True).decode('ascii')
            print(reload_sep_output)
            return True
        except Exception as e:
            print(e)
            return False

    def prepare_sampling(self):
        if not self.setup_ready:
            logger.error("Looks like environment is not ready for emon, please check your setup")
            self.results = None
            return False
        self.disable_sampling = False
        iniTime = time.time()
        # Information coming from -v and -M is needed by EDP post-processing tool
        dmidecode = "dmidecode > {}/dmidecode.txt".format(self.results)
        logger.info("Collecting dmidecode...")
        if self.verbose: logger.info("Running : {} ".format(dmidecode))
        iniTime = time.time()
        pdmidecode = subprocess.Popen(
            dmidecode, shell=True, executable='/bin/bash')
        while pdmidecode.poll() is None:
            time.sleep(0.1)
            endTime = time.time()
            if endTime - iniTime >= 5:
                if self.verbose:
                    logger.error("Waited for 5 seconds and failed to complete process, killing {} ".format(pdmidecode.pid))
                pdmidecode.kill()
        emonv_file = "{}/emon-v.dat".format(self.results)
        emonm_file = "{}/emon-m.dat".format(self.results)
        emonv = "{}; emon -v > {}".format(self.basecmd, emonv_file)
        emonM = "{}; emon -M > {}".format(self.basecmd, emonm_file)
        logger.info("Collecting emonV...")
        if self.verbose: logger.debug("Running : {} ".format(emonv))
        iniTime = time.time()
        pemonv = subprocess.Popen(emonv, shell=True, executable='/bin/bash')
        while pemonv.poll() is None:
            time.sleep(0.1)
            endTime = time.time()
            if endTime - iniTime >= 5:
                if self.verbose:
                    logger.error("Waited for 5 seconds and failed to complete emon-v data collection process, killing {} ".format(pemonv.pid))
                pemonv.kill()
                return False

        logger.info("Collecting emonM...")
        if self.verbose: logger.debug("Running : {} ".format(emonM))
        iniTime = time.time()
        pemonM = subprocess.Popen(emonM, shell=True, executable='/bin/bash')
        while pemonM.poll() is None:
            time.sleep(0.1)
            endTime = time.time()
            if endTime - iniTime >= 5:
                if self.verbose:
                    logger.error("Waited for 5 seconds and failed to complete emon-m data collection, killing {} ".format(pemonM.pid))
                pemonM.kill()
                return False

        if not self.input:
            putil = PlatformUtil()
            logger.info("Events file not specified. Trying to determine automatically by checking with dcsometrics server")
            sys.stdout.flush()
            self.input = putil.get_events_file(self.emonPath, emonv_file)
            if not self.input:
                logger.error("Events input file not found in {}, also, unable to download from dcso metrics server... Please pass events file using -e parameter and restart collection...".format(self.emonPath))
                return False
        return True
    
    def start_sampling(self):
        emondata_file = "{}/emon.dat".format(self.results)
        # The next command is to get actual data.
        emonR = "{}; emon -i {} > {} ".format(self.basecmd, self.input, emondata_file)
        if self.affinitize_core:
            emonR = "{}; numactl --physcpubind {} emon -i {} > {}".format(self.basecmd, self.affinitize_core, self.input, emondata_file)
        if self.verbose:  logger.debug("Running : {} ".format(emonR))
        iniTime = time.time()
        pemonR = subprocess.Popen(emonR, shell=True, preexec_fn=os.setsid, executable='/bin/bash')
        sampletime = 0
        try:
            logger.info("EMON started collecting traces")
            while pemonR.poll() is None:
                time.sleep(1)
                if self.verbose:
                    logger.info("data collection in progress {} ".format(sampletime))
                ch.terminator="\r"
                logger.info("Elapsed time : {}s   \r".format(sampletime))
                sys.stdout.flush()
                ch.terminator="\n"
                sampletime += 1
                if self.disable_sampling:
                    if self.verbose:
                        logger.info("Stopping the emon collector {} ".format(pemonR.pid))
                    os.killpg(os.getpgid(pemonR.pid), signal.SIGTERM)
        except KeyboardInterrupt:
            os.killpg(os.getpgid(pemonR.pid), signal.SIGTERM)
        except:
            os.killpg(os.getpgid(pemonR.pid), signal.SIGTERM)
        logger.info("EMON collection ended after {} secs".format(int(time.time() - iniTime)))

class RedirectCollector(BaseCollector):
    config = None
    def __init__(self, *args, **kwargs):
        super(RedirectCollector, self).__init__(*args, **kwargs)

    def prepare_sampling(self):
        self.config = COLLECTORS_CONFIG.get(self.toolname)
        try:
            timeoutSeconds = 2
            command = "command -v {}".format(self.config['binary'])
            if (sys.version_info > (3, 0)):
                subprocess.check_output(command, shell=True, timeout=timeoutSeconds)
            else:
                subprocess.check_output(command, shell=True)
            self.setup_ready = True
        except subprocess.CalledProcessError as grepexc:
            logger.error("Error while checking {},  return code {}".format(self.toolname, grepexc.returncode))
            logger.error("{} traces will not be collected".format(self.toolname))
            return False
        except Exception as e:
            logger.error("Error preparing {} collection, resulted in errror {}".format(self.toolname, str(e)))
            return False
        self.disable_sampling = False
        return True

    def start_sampling(self):
        outputfile = os.path.join(self.results,"{}.dat".format(self.toolname))
        toolcommand = "{} {} {} 2>&1 > {}".format(self.config['binary'], self.config['arguments'], self.config['samplingrate'], outputfile)
        if self.verbose:  
            logger.info("Running : {} ".format(toolcommand))
        iniTime = time.time()
        collectorProcess = subprocess.Popen(toolcommand, shell=True, preexec_fn=os.setsid, executable='/bin/bash')
        sampletime = 0
        try:
            logger.info("Started collecting {} traces".format(self.toolname))
            while collectorProcess.poll() is None:
                time.sleep(1)
                if self.disable_sampling:
                    if self.verbose:
                        logger.info("Stopping {} collector {} ".format(self.toolname, collectorProcess.pid))
                    os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        except KeyboardInterrupt:
            os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        except:
            os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        self.post_process()
        logger.info("{} collection ended after {} secs".format(self.toolname, int(time.time() - iniTime)))

    def post_process(self):
        if self.config.get('postprocess', None):
            logger.info("Found Post Processor for {} collector".format(self.toolname))
            logger.info("Running post processing for {} collector".format(self.toolname))
            try:
                command = self.config.get('postprocess', None)
                subprocess.check_output(command, shell=True)
            except Exception as e:
                logger.error("Error post processing the data from {}, resulted in errror {}".format(self.toolname, str(e)))
                return False
            logger.info("Completed post processing for {} collector".format(self.toolname))
            return True

class SarCollector(RedirectCollector):
    config = None
    def __init__(self, *args, **kwargs):
        super(SarCollector, self).__init__(*args, **kwargs)

    def start_sampling(self):
        tempoutput = os.path.join(self.results,"{}.bin".format(self.toolname))
        outputfile = os.path.join(self.results,"{}.dat".format(self.toolname))
        toolcommand = "{} {} {} -o {} > /dev/null ".format(self.config['binary'], self.config['arguments'], self.config['samplingrate'], tempoutput)
        if self.verbose:  
            logger.info("Running : {} ".format(toolcommand))
        iniTime = time.time()
        collectorProcess = subprocess.Popen(toolcommand, shell=True, preexec_fn=os.setsid, executable='/bin/bash')
        sampletime = 0
        try:
            logger.info("Started collecting {} traces".format(self.toolname))
            while collectorProcess.poll() is None:
                time.sleep(1)
                if self.disable_sampling:
                    if self.verbose:
                        logger.info("Stopping {} collector {} ".format(self.toolname, collectorProcess.pid))
                    os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        except KeyboardInterrupt:
            os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        except:
            os.killpg(os.getpgid(collectorProcess.pid), signal.SIGTERM)
        logger.info("{} collection ended after {} secs".format(self.toolname, int(time.time() - iniTime)))
        self.post_process(tempoutput, outputfile)
        os.system("rm -rf {}".format(tempoutput))

    def post_process(self, source, destination):
        if self.config.get('postprocess', None):
            logger.info("Found Post Processor for {} collector".format(self.toolname))
            logger.info("Running post processing for {} collector".format(self.toolname))
            try:
                command = self.config.get('postprocess', None)
                command = command.format(source, destination)
                subprocess.check_output(command, shell=True)
            except Exception as e:
                logger.error("Error post processing the data from {}, resulted in errror {}".format(self.toolname, str(e)))
                return False
            logger.info("Completed post processing for {} collector".format(self.toolname))
            return True


class MasterCollector(object):
    args = None
    requested_collectors = []
    collectors = {}
    results = None
    def __init__(self, pargs):
        self.args = pargs

    def prepare_environment(self):
        try:
            logger.info("Preparing environemnt....")
            telemetry = self.args.telemetry
            if telemetry: 
                if 'all' in telemetry.lower(): 
                    self.requested_collectors = list(COLLECTORS_CONFIG.keys())
                else:
                    for requested in telemetry.split(','):
                        if requested in COLLECTORS_CONFIG.keys(): 
                            if requested not in self.requested_collectors:
                                self.requested_collectors.append(requested)
                        else:
                            logger.warning("Requested collector {} not in supported collector list...")
            if not self.results:
                if self.args.dir:
                    if self.args.dest_dir_name:
                        self.results = os.path.join(self.args.dir, self.args.dest_dir_name)
                        self.results = get_unique_dir(self.results)
                    else:
                        self.results = os.path.join(self.args.dir, generate_dir_with_ts(self.args.append))
                else:
                    self.results = os.path.join(os.getcwd(), generate_dir_with_ts(self.args.append))
        except Exception as e:
            logger.error("Error while preparing the environment ...")
            logger.error(str(e))
            return False
        self.metadata_dir = os.path.join(self.results,'metadata')            
        try:
            os.makedirs(self.results)
        except OSError as e:
            if e.errno != errno.EEXIST:
                return False        
        return len(self.requested_collectors) > 0

    def display_telemetryfiles(self):
        logger.info("Results stored at {} ".format(self.results))
        output = ""
        try:
            op = subprocess.check_output(["ls", "-lrth", "-p", self.results])
            output = op.decode()
            for line in output.split("\n"):
                logger.info(line)
        except Exception as e:
            logger.error(e)
            logger.error(output)

    def get_data_path(self):
        return self.results

    def get_metadata_path(self):
        return self.metadata_dir

    def prepare_collectors(self):
        for collector in self.requested_collectors:
            config = COLLECTORS_CONFIG.get(collector, None)
            if config:
                collector_type = config.get("collector_type")
                if collector_type == "emon":
                    tcol = EmonCollector(self.results, collector, args=self.args)
                    if self.args.force_reload_sep:
                        logger.info("As requested Force reloading the SEP driver...")
                        tcol.reload_emon()
                elif collector_type == "redirect":
                    tcol = RedirectCollector(self.results, collector, self.args)
                elif collector_type == "sar":
                    tcol = SarCollector(self.results, collector, self.args)
                if tcol.is_already_inuse():
                    logger.error("The telemetry tool {} already running, please stop it before starting the telemetry collection using the respective tool.".format(collector))    
                    continue
                if tcol.prepare_sampling(): 
                    self.collectors[collector] = tcol
                elif collector_type == "emon": 
                    logger.error("Looks like the telemetry client failed to configure EMON Collection.. So, stopping all telemetry collection...")
                    return False
            else:
                logger.error("Collecting telemetry using requested tool {} is not supported yet by TMC.".format(collector))
                logger.error("Supporrted tools {}".format(COLLECTORS_CONFIG.keys()))
        return True

    def collect_metadata(self):
        try:
            os.makedirs(self.metadata_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise        
        metadata.collect(self.metadata_dir)

    def start(self):
        if not self.prepare_environment(): return False
        self.collect_metadata()
        if not self.prepare_collectors():
            logger.error("Failed to prepare telemetry collectors....")
            return False
        for cname, collector in self.collectors.items():
            try:
                collector.start()
            except Exception as e:
                logger.error("Exception while starting collector : {}".format(cname))
                logger.error(str(e))

    def stop(self):
        for cname, collector in self.collectors.items():
            try:
                collector.disable_sampling=True
            except Exception as e:
                logger.error("Exception while stopping collector : {}".format(cname))
                logger.error(str(e))
        for cname, collector in self.collectors.items():
            try:
                collector.stop()
            except Exception as e:
                logger.error("Exception while stopping collector : {}".format(cname))
                logger.error(str(e))

    def is_running(self):
        running = False
        for cname, collector in self.collectors.items():
            if collector.is_running(): running = True
        return running

    def wait_forever(self, collector_name='emon'):
        logger.info("{} collector will be running until user kills (ctrl+c).".format(collector_name))
        if collector_name not in self.collectors: 
            return
        while True:
            time.sleep(1)
            if not self.collectors[collector_name].is_running():
                break

def start_telmetry():
    pargs = parse_args()
    if pargs.verbose:
        logger.info(pargs)
    if pargs.upload and not pargs.non_interactive:
        logger.warning("For automation please enable '-n', '--non-interactive' flags, else user confirmation needed before uploading to the server")
    pHandler = ProcessHandler(pargs)
    collector = MasterCollector(pargs)
    if not collector.prepare_environment():
        logger.error("Error while preparing collection environment...")
        return False

    logfilehandle = None
    if pargs.target_cmd:
        logfile = os.path.join(collector.get_data_path(), "target_output.txt")
        logfilehandle = open(logfile, 'w+')
        if pargs.ramp_time <= 0:
            collector.start()
        if pargs.target_gap > 0:
            time.sleep(pargs.target_gap)
        pargs.process_id = pHandler.start_target(pargs, logfilehandle)

        if pargs.process_id:
            if pargs.ramp_time > 0:
                time.sleep(pargs.ramp_time)
                collector.start()
        else:
            logger.error("Failed to start the target process, stopping collector...")
            collector.stop()
    else:
        collector.start()

    try:
        if collector.is_running():
            if not pargs.process_id and pargs.time_duration == 0:
                collector.wait_forever()
            elif pargs.process_id:
                if not system_tools_available:
                    logger.error("Python's psutil module required to sync with with process execution duration.")
                    logger.error("Please install psutil package using pip 'pip install psutil'")
                    collector.wait_forever()
                else:
                    if pHandler.wait_for_target(pargs) == -1:
                        collector.wait_forever()
            else:
                time.sleep(pargs.time_duration)
                logger.info("Collection time out {}s reached, now ending data collection".format(pargs.time_duration))
    except KeyboardInterrupt:
        logger.info("Received user KeyboardInterrupt, Stopping emon")
    finally:
        collector.stop()
    collector.display_telemetryfiles()
    results_dir = collector.get_data_path()
    metadata.collect_postwl(collector.get_metadata_path())
    if pargs.upload and results_dir:
        pp = PostProcessor(pargs.verbose)
        pp.non_interactive_mode = pargs.non_interactive
        pp.start_edp_trace = pargs.start_trace
        pp.stop_edp_trace = pargs.end_trace
        pp.start_buoy_time = pargs.buoy_start_time
        pp.stop_buoy_time = pargs.buoy_stop_time
        pp.tps = pargs.tps
        pp.process(pargs.user, results_dir, pargs.chart_views, pargs.identity_comment, pargs.group, dest_subdir=pargs.dest_dir_name)
    else:
        logger.info("Telemetry data collection completed, but data not uploaded as user didn't specifcy -u option...!")

def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("{} is an invalid positive int value{} ".format(value))
    return ivalue

def check_affinitize_core(value):
    ivalue = int(value)
    if 0 <= ivalue and ivalue < multiprocessing.cpu_count():
        return ivalue
    raise argparse.ArgumentTypeError("{} is an invalid value to affinitze the emon, it must be 0 to {}".format(value, multiprocessing.cpu_count()-1))

def parse_args():
    parser = argparse.ArgumentParser(description='Process commandline arguments')
    parser.add_argument('-a', '--append', help='Append this string to sample name', default=None, type=str)
    parser.add_argument('-b', '--binary-emon', help='Emon installation path. Default : /opt/intel/sep', default='/opt/intel/sep', type=str)
    parser.add_argument('-c', '--target-cmd', help='Target command to start after stating the Emon', default=None, type=str)
    parser.add_argument('-d', '--dir', default=os.path.join(os.getcwd(), "traces"), help='Output directory where the emon traces to be stored. Default - current working directory', type=str)
    parser.add_argument('-e', '--events-file', help='Emon events file. If not provided and its not available in system then it will try to download from dungeon share', default='', type=str)
    parser.add_argument('-g', '--target-gap', help='Time (sec) to wait before starting the target command. Default 1 (valid only with --target-cmd option)', default=0, type=check_positive)
    parser.add_argument('-i', '--identity-comment', help='Comment to identify the emon logs in server', default=None, type=str)
    parser.add_argument('-n', '--non-interactive', action='store_true', help='Push data in non-interactive mode (without user confirmation), useful for automations')
    parser.add_argument('-o', '--max-timeout', help='Max time (sec) to wait for a target process to finish. default=0 (i.e. forever) (valid only with --process-id option)', default=0, type=check_positive)
    parser.add_argument('-p', '--process-id', help='Target process ID that collector has to wait to stop. Default None', default=None, type=int)
    parser.add_argument('-r', '--ramp-time', help='Time (sec) to wait before collecting data. Default 0 (valid only with --target-cmd option)', default=0, type=check_positive)
    parser.add_argument('-s', '--time-stamp', help='timestamp value that has to added into the output dir. Default autogenerated', default='', type=str)
    parser.add_argument('-t', '--time-duration', help='Amount of duration to collect the data. Default 0 (i.e. forever until user pressed ctl+c)', default=0, type=check_positive)
    parser.add_argument('-u', '--upload', action='store_true', help='Enable uploading the traces to server after ending')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logs')
    parser.add_argument('-w', '--chart-views', help='Kind of chart views (thread, core, socket, uncore) to be processed in remote server -w socket | -w socket,uncore | -w thread,socket,core -w thread,core | -w core', default="socket,uncore", type=str)
    parser.add_argument('-x', '--user', help='Username to be tagged in DCSO metrics server', default=None, type=str)

    parser.add_argument('-D', '--dest-dir-name', help='Destination sub directory where the emon traces to be pushed.', default=None, type=str)
    parser.add_argument('-G', '--group', help='provide group name to your emon trace, this is useful to group your traces on server side', default="Global", type=str)    

    parser.add_argument('-A', '--buoy-start-time', default=1, help='Provide start time for buoy in seconds.', type=check_positive)
    parser.add_argument('-B', '--buoy-stop-time', default=1500000, help='Provide end time for buoy in seconds.', type=check_positive)
    parser.add_argument('-S', '--start-trace', default=1,help='Provide start sample number for edp.',  type=check_positive)
    parser.add_argument('-E', '--end-trace', default=1500000,help='Provide end sample number for edp.', type=check_positive)
    parser.add_argument('-X', '--tps', default=0,help='Providing TPS will process EDP & buoy with provided TPS value. Bulk processing will ignore this',  type=check_positive)
    parser.add_argument('-T', '--telemetry', help='List of telemetries to collect (e.g. -T all | -T emon | -T emon,sar | -T emon,sar,iostat) to be collected (Default : emon)', default='all', type=str)
    parser.add_argument('-k', '--affinitize-core', default=None, help='Affinitize emon to run on specfic core with numactl (note numactl must be installed on the system). core range must be within logical CPUs range', type=check_affinitize_core)
    parser.add_argument('-f', '--force-reload-sep', action='store_true', help='If existing emon collector running then reload sep to kill old process.')

    pargs = parser.parse_args()
    return pargs

if __name__ == '__main__':
    logger.warning("****** TMC is still in alpha stage and may have bugs, if you find any issue please report it ******")
    logger.warning("We highly recommend using latest (i.e. git pull) TMC to enjoy latest features.")
    start_telmetry()
