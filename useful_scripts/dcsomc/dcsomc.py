import argparse
import json
import logging
import os.path
import re
import socket
import subprocess
import sys
from argparse import Namespace
from inspect import getsourcefile
from subprocess import PIPE, Popen
from easysettings import EasySettings

os.environ["PYTHONUNBUFFERED"] = "1"

import requests
from requests.exceptions import HTTPError, RequestException
from termcolor import colored

from analyzer import TraceAnalyzer

VERSION=0.3

DEBUG_SERVER=False

USER = "dcso"
PASS = "intel321"
#SERVER = "dcsometrics.amr.corp.intel.com"
SERVER = "JF5300-B11A321T.jf.intel.com"

#SERVER = "dcsometrics2.amr.corp.intel.com"

#IP="10.242.51.131"
IP="10.165.84.26"
WEB_PORT="80"

logger = logging.getLogger('dcsomc')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)-8s- %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Version : {}".format(VERSION))
API_SERVER_HOSTNAME = "http://{}:{}".format(SERVER, WEB_PORT)
API_SERVER_IP = "http://{}:{}".format(IP, WEB_PORT)

PLATFORM_CODES = {"sandybridge": "snb", "ivybridge": "ivb", "haswell": "hsw", "broadwell": "bdw",
                  "skylake": "skx", "cascadelake": "clx", "cooperlake": "cpx", "icelake": "icx", "snowridge": "snr"}

dcsomc_path = os.path.dirname(os.path.realpath(__file__))
setting_file_name = os.path.join(dcsomc_path, ".dcsomc.conf")
settings = EasySettings(setting_file_name)

class Utils(object):

    def __init__(self, *args, **kwargs):
        super(Utils, self).__init__(*args, **kwargs)

    def run_command(self, cmd):
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
            output = ""
            l = ""
            for c in iter(lambda: p.stdout.read(1), b''):
                c = c.decode(sys.stdout.encoding)
                output += c
                if c in ["\r", "\n"]:
                    logger.info(l)
                    l = ""
                else:
                    l += c
            l = ""
            for c in iter(lambda: p.stderr.read(1), b''):
                c = c.decode(sys.stdout.encoding)
                output += c
                if c in ["\r", "\n"]:
                    logger.error(l)
                    l = ""
                else:
                    l += c
            return output
        except:
            raise

    def download(self, URL, dst, ask_confirmation=True):
        import socket
        import requests
        response = None
        try:
            if socket.gethostbyname(socket.gethostname()).startswith(('8', '9', '7')):
                response = requests.get(URL, stream=True, proxies=None)
            else:
                response = requests.get(URL, stream=True)
            if response.status_code == 200:
                filename = response.headers.get("filename", "myevents.txt")
                dst_file = os.path.join(dst, filename)
                if os.path.exists(dst_file):
                    logger.debug("Event file already exists : {}".format(dst_file))
                    return dst_file
                if ask_confirmation: 
                    if not self.get_interactive_yesno("\nINFO : Server sent {} events file with detected Family, Model, Stepping...\n\n Do you want to use it ?".format(filename)):
                        return False
                logger.info("Saving events file from server into : {}".format(dst_file))
                with open(dst_file, 'wb') as f:
                    for chunk in response:
                        f.write(chunk)
                return dst_file
            else:
                return False
        except Exception as e:
            logger.error(e)
            return None
        finally:
            if response:
                response.close()

    def post_data(self, endpoint, data, max_tries=2):
        url = "{}/{}".format(API_SERVER_HOSTNAME, endpoint)
        proxies = {
        "http": None,
        "https": None,
        }
        data['cversion'] = VERSION
        for n in range(max_tries):
            try:
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                response = requests.post(url = url, data=json.dumps(data), proxies=proxies, headers=headers)
                response.raise_for_status()
                jsonResponse = response.json()
                if "error" in jsonResponse:
                    logger.error("Server returned error : {}".format(jsonResponse["error"]))
                return jsonResponse
            except RequestException as e:
                error = "{}".format(e)
                if "failure in name resolution" in error:
                    logger.error("DNS Failure, trying with IP")
                    url = "{}/{}".format(API_SERVER_IP, endpoint)
                else:
                    import time
                    if n == max_tries - 1:
                        raise
                    logger.error("Error while communicating with the server: {}, retrying in 5 seconds ".format(e))
                    time.sleep(5)
            except Exception as e:
                logger.error('Other error occurred: {}'.format(e))

    def valid_user(self, username):
        data = {'username': username}
        response = self.post_data("client_check_user", data)
        if "result" in response:
            result = response.get("result")
            if "valid" == result.lower():
                return True
            else:
                logger.error("Server responsed as {}".format(result))
                return False
        else:
            logger.error(response)
            return False

    def get_username(self):
        while True:
            header="Please input username (Intel Windows username) that this trace will be tracked against in DCSO Metrics"
            logger.info(header)
            try:
                try:
                    input_fn = raw_input
                except Exception as e:
                    input_fn = input
                    pass
                answer = None
                answer = input_fn("Username (without AMR/GAR) : ")
                answer = answer.strip()
                if answer:
                    if self.valid_user(answer):
                        logger.debug("User found on server side ....")
                        return answer
                    else:
                        logger.error("Invalid username... please provide valid username...")
                        return None
                else:
                    logger.error("Please input valid user that can be checked against DCSO metrics")
            except Exception as e:
                logger.error(e)
                return None

    def configure_user(self, current_user=None):
        if current_user:
            if not self.valid_user(current_user):
                logger.error("Invalid user provided")
                current_user = self.get_username()
        elif settings.has_option('current-user'):
            current_user = settings.get('current-user')
            banner = "Using previously configured username {} for uploading the data.. To change username pls run with --user option".format(colored(current_user, 'blue'))
            logger.warning(banner)
        else:
            current_user = self.get_username()
        if current_user:
            settings.setsave('current-user', current_user)
            return current_user
        else:
            return None

    def get_interactive_yesno(self, question, default="yes"):
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            logger.error("invalid default answer: '{}'".format(default))
            raise ValueError("invalid default answer: '{}'".format(default))

        while True:
            sys.stdout.write(question + prompt)
            try:
                input_fn = raw_input
            except Exception as e:
                input_fn = input
                pass
            answer = None
            choice = input_fn().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                logger.info("Please confirm with 'yes' or 'no' ""(or 'y' or 'n').\n")

    def get_file_content(self, URL):
        import socket
        import requests
        response = None
        try:
            if socket.gethostbyname(socket.gethostname()).startswith(('8', '9', '7')):
                response = requests.get(URL, stream=True, proxies=None)
            else:
                response = requests.get(URL, stream=True)
            if response.status_code == 200:
                resp = json.loads(response.text)
                return resp
            return None
        except Exception as e:
            logger.error(e)
            return None
        finally:
            if response:
                response.close()

class PlatformUtil(object):
    lscpu_output = None
    platform = None
    def __init__(self, util=None):
        self.lscpu_output = __import__('subprocess').check_output('lscpu', shell=True).decode('ascii')
        self.lscpu_result = {}
        if util:
            self.utils = util
        else:
            self.utils = Utils()
        for item in self.lscpu_output.strip().split("\n"):
            items = item.split(":")
            self.lscpu_result[items[0]] = " ".join(items[1:])

    def get_stepping(self):
        return int(self.lscpu_result["Stepping"].strip())

    def get_cpu_family(self):
        return int(self.lscpu_result["CPU family"].strip())

    def get_cpu_model(self):
        return int(self.lscpu_result["Model"].strip())

    def get_sockets(self):
        return int(self.lscpu_result["Socket(s)"].strip())

    def find_platform(self, emonv_file):
        long_name = None
        short_name = None
        p = r"EMON Database ([\.]+) ([^\n]+)_server"
        with open(emonv_file, 'r') as f:
            pat = re.search(p, f.read(), re.MULTILINE)
            if pat:
                long_name = pat.group(2)
        if long_name:
            short_name = PLATFORM_CODES.get(long_name.lower(), None)
        self.platform = long_name
        return long_name, short_name

    def get_events_file(self, dst, emonv_path):
        events_file = None
        dst_file = None
        if settings.has_option('events-file'):
            dst_file = settings.get('events-file')
        if dst_file and os.path.exists(dst_file):
            logger.info("Using existing events file : {}".format(dst_file))
            events_file = dst_file
        else:
            sockets = self.get_sockets()
            long_name, short_name = self.find_platform(emonv_path)
            default_file_name = "{}-{}s-events.txt".format(short_name, sockets)
            dst_file = os.path.join(dst, default_file_name)
            if os.path.exists(dst_file):
                logger.info("Using existing events file : {}".format(dst_file))
                events_file = dst_file
            else:
                events_file = self.fetch_required_eventsfile(dst)
        if events_file:
            settings.setsave('events-file', events_file)
        return events_file

    def fetch_required_eventsfile(self, dst):
        try:
            family = self.get_cpu_family()
            model = self.get_cpu_model()
            stepping = self.get_stepping()
            sockets = self.get_sockets()
            check_required_file = '{}/client_get_required_events?cversion={}&fms={},{},{}&sockets={}'.format(API_SERVER_HOSTNAME, VERSION,  family, model, stepping, sockets)
            required_file = self.utils.get_file_content(check_required_file)
            if "filename" in required_file:
                filename = required_file.get("filename")
                dst_file = os.path.join(dst, filename)
                if os.path.exists(dst_file):
                    logger.info("Using existing events file : {}".format(dst_file))
                    return dst_file
                if self.utils.get_interactive_yesno("INFO : Server recommending to use following events file based on this system Family, Model, Stepping information...\n\n {}  \n\nDo you want to use it? Y - Download and use, N - Show all available files...".format(filename)):
                    events_file = '{}/client_get_events_file?cversion={}&fms={},{},{}&sockets={}'.format(API_SERVER_HOSTNAME, VERSION,  family, model, stepping, sockets)
                    logger.info("Checking for SEP events file for family: {}, model {}, stepping {}, sockets {}".format(family, model, stepping, sockets))
                    return self.utils.download(events_file, dst, False)
                else:
                    check_required_file = '{}/client_get_required_events?cversion={}&fms={},{},{}&sockets={}'.format(API_SERVER_HOSTNAME, VERSION,  0, 0, 0, sockets)
                    required_file = self.utils.get_file_content(check_required_file)
            if "available" in required_file:
                server_list = required_file.get("available")
                server_list = server_list + ['Abort Collection']
                user_selected_file = self.get_userinput(server_list)
                if user_selected_file == "Abort Collection":
                         False
                settings.setsave("edp_resource", user_selected_file)
                if not user_selected_file:  return False
                events_file = '{}/client_get_events_file?cversion={}&userselected={}'.format(API_SERVER_HOSTNAME, VERSION, user_selected_file)
                logger.info("Downloading user selected events file {} from server".format(user_selected_file))
                return self.utils.download(events_file, dst, False)
        except Exception as e:
            logger.error(e)
            return False

    def show_available_eventsfile(self):
        try:
            check_required_file = '{}/client_get_required_events'.format(API_SERVER_HOSTNAME)
            required_file = self.utils.get_file_content(check_required_file)
            if "available" in required_file:
                header="List of event files available in current server database"
                print("*" * len(header))
                options = required_file.get("available")
                for i, option in enumerate(options, 1):
                    print('{}. {}'.format(i,option))
                print("*" * len(header))
        except Exception as e:
            logger.error(e)
            return False

    def get_userinput(self, options):
        while True:
            header="Pick the events file from available list"
            print("*" * len(header))
            for i, option in enumerate(options, 1):
                print('{}. {}'.format(i,option))
            try:
                answer = input("\nPick the events file from above list\nUser Choice : ")
                answer = int(answer)
                if 1 <= answer <= len(options):
                    return options[answer-1].replace("<","").strip()
                print("That option does not exist! Try again!")
            except ValueError:
                print("Doesn't seem like a number! Try again!")


class PostProcessor(object):

    reverse_rsync_command = ""
    def __init__(self, verbose=False):
        self.hostname = socket.gethostname()
        self.utils = Utils()
        self.platformutil = PlatformUtil(self.utils)
        self.verbose = verbose
        self.traceanalyzer = TraceAnalyzer(self.verbose)
        self.platform = None
        self.non_interactive_mode = False
        self.start_edp_trace = 1
        self.stop_edp_trace = 15000000
        self.start_buoy_time = 1
        self.stop_buoy_time = 15000000
        self.tps = 0

    def rsync_directory(self, source, destination, excludeFile=None, dryRun=False, showProgress=True):
        dest = "{}:{}".format(SERVER, destination)
        logger.info("Pushing the results from {}  to {} ".format(source, dest))
        command = 'rsync -ratlO --rsh="sshpass -p ' + PASS + \
            ' ssh -o PreferredAuthentications=password -o StrictHostKeyChecking=no -l ' + USER + '" ' + source + '/ ' + dest
        if excludeFile != None:
            command += ' --exclude-from=' + excludeFile
        if dryRun:
            command += ' --dry-run'
        if showProgress:
            command += ' --progress'
        self.reverse_rsync_command = "rsync -ratlz {}@{}/ {} --progress".format(USER, dest, source)
        try:
            self.utils.run_command(command)
            return True
        except Exception as e:
            logger.error(e)
        return False

    def emd_server_get_destination(self, username, subdir, group, tracename):
        family = self.platformutil.get_cpu_family()
        model = self.platformutil.get_cpu_model()
        stepping = self.platformutil.get_stepping()
        sockets = self.platformutil.get_sockets()
        fms="{},{},{}".format(family, model, stepping)
        request_data = {'name': tracename, 'username': username, 'hostname': self.hostname, 'subdir': subdir, 'groupname': group, 'grouppath': group, "fms": fms}
        response = self.utils.post_data("client_handshake", request_data)
        if 'error' in response:
            logger.error("Server returned error on directory path request:")
            logger.error(response.get('error'))
            return None, tracename
        else:
            destpath = response.get('path', None)
            updatedname = response.get('updatedname', None)
            if not self.platform: self.platform = response.get('platform', None)
            return destpath, updatedname
        return None, None

    def get_views(self, string):
        views = {}
        for view in string.split(","):
            views.update({view: True})
        return {'socketview': views.get("socket", False), 'threadview': views.get("thread", False), 'coreview': views.get("core", False),'uncoreview': views.get("uncore", False)}

    def get_user_confirmation(self, request_data):
        logger.info("The directory will be processed with below configuration on the server")
        for key, value in request_data.items():
            logger.info("%-15s : %s" % (key.capitalize(), value))
        if self.non_interactive_mode:
            return True 
        return self.utils.get_interactive_yesno("Are you sure you want to upload data to process with above parameters:")

    def emd_server_start_processing(self, username, source, destination, views, name, comment, group, bulktrace, reprocess_group, group_traces, sockets):
        if not self.platform:
            logger.warning("Server failed to determine platform information...Please check if processor using proper EDP resources...")
        views = self.get_views(views)
        if not comment:
            comment = "N/A"
        edp_resource = None
        if settings.has_option('edp_resource'):
            edp_resource = settings.get('edp_resource')
        clip = {'start':self.start_edp_trace, 'end':self.stop_edp_trace,'buoystart':self.start_buoy_time, 'buoystop':self.stop_buoy_time}
        request_data = {
            'name': name,
            'username': username,
            'hostname': self.hostname,
            'path': destination,
            'sockets': sockets,
            'platform': self.platform,
            'tps' : self.tps,
            'edp_resource': edp_resource,
            'views': json.dumps(views), 'comment': comment, 'group': json.dumps(group), 'clip': json.dumps(clip), 'bulktrace': bulktrace, 'reprocessgroup': reprocess_group, 'group_traces': group_traces}
        useranswer = self.get_user_confirmation(request_data)
        if not useranswer:
            logger.info("User cancelled upload")
            return
        if not self.rsync_directory(source, destination):
            logger.error("Failed to push the emon traces to server, not starting the edp processing")
            return False
        logger.info("Collected traces succesfully pushed into server @ {}{}{}".format(SERVER, destination, name))
        logger.info("Sending request to start metrics processing")
        request_data["cversion"]=VERSION
        response = self.utils.post_data("client_start_processing", request_data)
        if 'error' in response:
            logger.error("Server failed to process the uploaded EMON Traces")
            logger.error(response.get('error',"unknown error"))
        else:
            SERVER_LINK = colored("https://{}".format(SERVER), 'green', attrs=['blink'])
            BROWSER_LINK = colored(response.get('outputurl'), 'blue')
            SAMBA_SHARE = response.get("samba_share","")
            WINDOWS_SHARE ="\\\\{}{}".format(SERVER, SAMBA_SHARE).replace(r"/","\\")
            WINDOWS_SHARE = colored(WINDOWS_SHARE, 'blue' )
            RSYNC_COMMAND = colored(self.reverse_rsync_command, 'blue')
            record_ids=response.get('record_ids',[])
            logger.info("Processing requested successfully accepted by DCSO metrics server")
            logger.info("Check processing status & detailed logs in DCSO Metrics Portal")
            logger.info(SERVER_LINK)
            logger.info("Browser link  (Access in Browser)")
            logger.info(BROWSER_LINK)
            logger.info("Network share (Access from Windows PC, dcso/intel321)")
            logger.info(WINDOWS_SHARE)
            logger.info("RSYNC results (passwd :  intel!321)")
            logger.info(RSYNC_COMMAND)
            for record in record_ids:
                RECORD_LINK="Metrics Record - https://{}/record?id={}".format(SERVER,record)
                logger.info(RECORD_LINK)

    def process(self, inputuser, source, views, comment, group, bulktrace=False, reprocess_group=False, dest_subdir=None, sockets=None):
        username = self.utils.configure_user(inputuser)
        if not username:
            logger.error("Valid Windows username requried to uploaded traces to DCSO metrics server!")
            return False
        tracename = os.path.basename(os.path.normpath(source))
        tracename = tracename.strip().replace(" ","_")
        group_traces=[]
        if bulktrace:
            group_traces, missing = self.traceanalyzer.analyze_nested_dirs(source)
            if len(group_traces) == 0:
                logger.error("Analyzer says no valid trace sub directories available to push, please check if the traces are valid or file bug for dcsomc.analyzer bug")
                return False
            if missing > 0:
                logger.warning("Analyzer found some sub directories without completed emon trace files. These sub-directories will be pushed to server but will not be processed.")
        else:
            if not self.traceanalyzer.analyze_dir(source):
                logger.error("Analyzer says its not a valid trace directories to push, please check if the trace is valid or file bug for dcsomc.analyzer bug")
                return False
        if len(self.traceanalyzer.platform) != 1: 
            logger.error("Unfortunatley server can't do heterogeneous trace processing on signle request. Please try sending each platform sepereatly.. ")
            logger.error("Detected platforms from emon-v.dat/emon.dat traces are {}".format(self.traceanalyzer.platform))
            return False
        if self.traceanalyzer.platform == 0:
            logger.error("Unable to find platform info from emon files... Pleas specify manually...")
            return False
        self.platform = self.traceanalyzer.platform[0]
        edp_resource = settings.get('edp_resource')
        if "AMD" in self.traceanalyzer.platform and (not edp_resource): 
            logger.error("Hey.. Sorry.. Metrics server does not support auto detection of required EDP resource for AMD emon traces... please specify the EDP resource using '-e' param")
            logger.error("It must be specified something like dcsomc -e '/AMD/Zen2/zen2-events.txt' ")
            return False
        logger.debug("-------------- Handshake with dcsometrics server --------------")
        # For bulk traces (more than 1 trace) don't send trace name and dest sub dir param
        if bulktrace:
            if group != "Global":
                tracename=None
        # if user specifying a directory name for server side then don't send trace name to get_destination API call
        if dest_subdir:
            dest_subdir = dest_subdir.strip().replace(" ","_")
            tracename = None
        destination, tracename = self.emd_server_get_destination(username=username, subdir=dest_subdir, group=group, tracename=tracename)
        if not destination:
            logger.error("Server didn't ack your destination request, please check error logs")
            return False
        if bulktrace:
            groupins = {"name": group, 'path' : destination}
        else:
            groupins = {"name": group, 'path' : destination.replace(tracename, "")}
        if not sockets:
            sockets=self.platformutil.get_sockets()
        self.emd_server_start_processing(username, source, destination, views, tracename, comment, groupins, bulktrace, reprocess_group, group_traces, sockets)

def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("{} is an not a valid input, it must be greater than 0".format(value))
    return ivalue

def check_nonneg(value):
    ivalue = float(value)
    if ivalue <= -1:
        raise argparse.ArgumentTypeError("{} is a negative number".format(value))
    return ivalue

def parse_args():
    parser = argparse.ArgumentParser(description='cmd arguments parser')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-l', '--events-list', action='store_true')
    parser.add_argument('-e', '--edp-resource', help='Provide the EDP events file that was used to collect the emon traces (Use "dcsomc -l" to see available list)', default=None, type=str)
    parser.add_argument('-n', '--non-interactive', action='store_true', help='Push data in non-interactive mode (without user confirmation), useful for automations')
    parser.add_argument('-H', '--hostname', help='Specify hostname where the trace was collected.', default=None, type=str)
    parser.add_argument('-p', '--platform', help='Specify what platform the trace was collected.', default=None, type=str)
    parser.add_argument('-s', '--sockets', default=None, type=check_positive)
    parser.add_argument('-S', '--start-trace', default=1,help='Provide start sample number for edp.',  type=check_positive)
    parser.add_argument('-E', '--end-trace', default=1500000,help='Provide end sample number for edp.', type=check_positive)
    parser.add_argument('-A', '--buoy-start-time', default=1, help='Provide start time for buoy in seconds.', type=check_positive)
    parser.add_argument('-B', '--buoy-stop-time', default=1500000, help='Provide end time for buoy in seconds.', type=check_positive)
    parser.add_argument('-X', '--tps', default=0, help='Providing TPS will process EDP & buoy with provided TPS value. Bulk processing will ignore this.', type=check_nonneg)
    parser.add_argument('-d', '--dir', help='Output directory from where the emon traces to be pushed.', default=None, type=str)
    parser.add_argument('-D', '--dest-dir-name', help='Destination sub directory where the emon traces should be store in DCSO Metrics server', default=None, type=str)
    parser.add_argument('-b', '--bulk-traces', action='store_true', help='Tell this is a group root directory and server to process all the traces')
    parser.add_argument('-G', '--group', help='Group name to to organzie bunch of emon traces', default="Global", type=str)
    parser.add_argument('-r', '--reprocess-group', help='Should the existing traces in the group be reprocessed along with the new traces.', action="store_true")
    parser.add_argument('-i', '--identity-comment', help='Comment to track against each emon trace', default='', type=str)
    parser.add_argument('-x', '--user', help='Username to be tagged in DCSO metrics server', default=None, type=str)
    parser.add_argument('-w', '--chart-views',  help='Kind of chart views (thread, core, socket) to be processed in remote server -w socket | -w socket,uncore | -w thread,socket,core -w thread,core | -w core', default="socket,uncore", type=str)
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        print("\nAdding workload results into score column.")
        print("Create a file with name with prefix \"workload_result\" and include your workload results & configuration data that is seperated with ':'.. Metrics will store it in database \n") 
        print("  root@JF5300-B11A167T:~# cat workload_result.txt \n  workload_name:\"TF RN50 AMX BF16\" \n  metric_type:\"Throughput\" \n  result:\"15000\" \n  metric:\"img/s\"\n  num_instances:2 \n  sockets:2 \n  notes:\"Running TF with memory knob changes\"\n")
        sys.exit(1)
    pargs = parser.parse_args()
    return pargs

def run_postprocessor():
    pargs = parse_args()
    if pargs.verbose:
        logger.info("Input Params")
        logger.info(pargs)
    logger.warning("It's recommended using latest (i.e. git pull) DCSO Client to have better experience.")
    if pargs.events_list:
        platutil = PlatformUtil()
        platutil.show_available_eventsfile()
    if pargs.edp_resource:
        settings.setsave("edp_resource", pargs.edp_resource)
    if pargs.dir:
        pp = PostProcessor(pargs.verbose)
        if pargs.hostname:
            pp.hostname = pargs.hostname
        pp.non_interactive_mode = pargs.non_interactive
        pp.start_edp_trace = pargs.start_trace
        pp.stop_edp_trace = pargs.end_trace
        pp.start_buoy_time = pargs.buoy_start_time
        pp.stop_buoy_time = pargs.buoy_stop_time
        pp.tps = pargs.tps
        if pargs.platform:
            pp.platform = pargs.platform
        pp.process(pargs.user, pargs.dir, pargs.chart_views, pargs.identity_comment, pargs.group, pargs.bulk_traces, pargs.reprocess_group, pargs.dest_dir_name, pargs.sockets)

if __name__ == '__main__':
    run_postprocessor()
