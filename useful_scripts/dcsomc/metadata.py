import os
import sys
import errno
import time
import subprocess
import logging

VERSION=0.1

logger = logging.getLogger('metadata')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)-8s- %(levelname)s - %(message)s',"%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Version : {}".format(VERSION))

metadata_providers = {
    "release": {
        "cmd": "/etc/*-release",
        "type": 'redirect',
        "optional": False},
    "cmdline": {
        "cmd": "/proc/cmdline",
        "type": 'redirect',
        "optional": False},
    "cpuinfo": {
        "cmd": "/proc/cpuinfo",
        "type": 'redirect',
        "optional": False},
    "meminfo": {
        "cmd": "/proc/meminfo",
        "type": 'redirect',
        "optional": False},
    "partitions": {
        "cmd": "/proc/partitions",
        "type": 'redirect',
        "optional": False},
    "scsi": {
        "cmd": "/proc/scsi/scsi",
        "type": 'redirect',
        "optional": False},
    "version": {
        "cmd": "/proc/version",
        "type": 'redirect',
        "optional": False},
    "modules": {
        "cmd": "/proc/modules",
        "type": 'redirect',
        "optional": False},
    "mounts": {
        "cmd": "/proc/mounts",
        "type": 'redirect',
        "optional": False},
    "interrupts": {
        "cmd": "/proc/interrupts",
        "type": 'redirect',
        "optional": False},
    "kernel_config": {
        "cmd": "/boot/config-$(uname -r)",
        "type": 'redirect',
        "optional": False},
    "sysctl_user": {
        "cmd": "/etc/sysctl.conf",
        "type": 'redirect',
        "optional": False},
    "hugepage_enable": {
        "cmd": "/sys/kernel/mm/*transparent_hugepage/enabled",
        "type": 'redirect',
        "optional": False,
    },
    "hugepage_defrag": {
        "cmd": "/sys/kernel/mm/*transparent_hugepage/defrag",
        "type": 'redirect',
        "optional": False,
    },
    "sar_version": {
        "cmd": "sar -V",
        "type": 'run',
        "optional": False},
    "date_timestamp": {
        "cmd": "date",
        "type": 'run',
        "optional": False},
    "hdparm": {
        "cmd": "hdparm -I /dev/sd*",
        "type": 'run',
        "optional": False},
    "dmidecode": {
        "cmd": "dmidecode",
        "type": 'run',
        "optional": False},
    "lspci": {
        "cmd": "lspci -tv", 
        "type": 'run',
        "optional": False},
    "lspci_full": {
        "cmd": "lspci -nnmmvk",
        "type": 'run',
        "optional": False},
    "uname": {
        "cmd": "uname -a",
        "type": 'run',
        "optional": False},
    "numactl": {
        "cmd": "numactl --hardware",
        "type": 'run',
        "optional": False},
    "hostname": {
        "cmd": "hostname",
        "type": 'run',
        "optional": False},
    "ifconfig": {
        "cmd": "ifconfig",
        "type": 'run',
        "optional": False},
    "dmesg": {
        "cmd": "dmesg -Txd",
        "type": 'run',
        "optional": False},
    "lsblk": {
        "cmd": "lsblk -a",
        "type": 'run',
        "optional": False},
    "lscpu": {
        "cmd": "lscpu",
        "type": 'run',
        "optional": False},
    "cpupower_idle": {
        "cmd": "cpupower idle-info",
        "type": 'run',
        "optional": False},
    "cpu_governor": {
        "cmd": 'find /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -V -k1 | xargs -i grep -H -i -v " " {} ',
        "type": 'run',
        "optional": False},
    "lsusb": {
        "cmd": "lsusb -v", 
        "type": 'run',
        "optional": False},
    "lsmod": {
        "cmd": "lsmod",
        "type": 'run',
        "optional": False},
    "nstat": {
        "cmd": "nstat -az",
        "type": 'run',
        "optional": False},
    "netstat": {
        "cmd": "netstat -sn",
        "type": 'run',
        "optional": False},
    "iptables": {
        "cmd": "iptables -L",
        "type": 'run',
        "optional": False},
    "irqbalance": {
        "cmd": "systemctl status --no-pager irqbalance", 
        "type": 'run',
        "optional": False},
    "getenforce": {
        "cmd": "getenforce",
        "type": 'run',
        "optional": False},
    "sysctl": {
        "cmd": "sysctl -a",
        "type": 'run',
        "optional": False},
    "smp_affinity": {
        "cmd": 'find /proc/irq/ -iname "*smp_affinity*" -print -exec cat {} \\;',
        "type": 'run',
        "optional": True},
    "module_parameters": {
        "cmd": "find /sys/module/*/parameters/* -print -exec cat {} \\;",
        "type": 'run',
        "optional": True},
    "ulimit": {
        "cmd": "ulimit -a", 
        "type": 'run',
        "optional": False},
    "boot_md5sum": {
        "cmd": "md5sum /boot/*",
        "type": 'run',
        "optional": True},
    "ppins": {
        "cmd": "modprobe msr;rdmsr -a 0x4f | sort -u | uniq",
        "type": 'run',
        "optional": False},
}

post_wl_metadata_providers = ['dmesg']

def write_to_file(outputfile, data):
    with open(outputfile, "a") as file:
        file.write(data)
        file.write("\n")

def run_command(command, metadata=None, outputfile=None):
    try:
        timeoutSeconds = 5
        if (sys.version_info > (3, 0)):
            subprocess.run(command, shell=True, timeout=timeoutSeconds)
        else:
            subprocess.check_output(command, shell=True)
    except Exception as e:
        logger.error("Error collecting metadata for {}".format(metadata))
        if outputfile:
            write_to_file(outputfile, "Error collecting metadata for {}".format(metadata))
            write_to_file(outputfile, str(e))


def collect_using_commands(commands_list, output_dir):
    for key, values in commands_list.items():
        ch.terminator="\r"
        logger.info("Collecting Metadata ... {} \r".format(key))
        sys.stdout.flush()
        ch.terminator="\n"
        value = values["cmd"]
        if values["optional"]:
            continue
        start = time.time()
        outputfile = os.path.join(output_dir, key)
        command = "{} 2>&1 > {}.txt".format(value, outputfile)
        if values['type'] == 'redirect':
            command = "cat {}".format(command)
        run_command(command, key, outputfile)

def collect(resultsdir):
    try:
        collect_using_commands(metadata_providers, resultsdir)
        marker_command = "echo \"TMC: INFO - ******************* Metadata collected, starting workload ***********************\" > /dev/kmsg"
        run_command(marker_command)
        logger.info("Collecting Metadata ... Completed successfully")
        logger.info("Metadata files stored in {} \r".format(resultsdir))
    except Exception as e:
        logger.error("Error collecting metadata")
        logger.error(str(e))

def collect_postwl(resultsdir):
    pwl_metdata_providers = {}
    try:
        for item in post_wl_metadata_providers:
            if item in metadata_providers.keys():
                pwl_metdata_providers["{}_afterwl".format(item)] = metadata_providers[item]
        collect_using_commands(pwl_metdata_providers,resultsdir)
    except Exception as e:
        logger.error("Error collecting metadata")
        logger.error(str(e))

if __name__ == '__main__':
    output_dir = "/tmp/raj"
    try:
        os.makedirs(output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    collect(output_dir)
