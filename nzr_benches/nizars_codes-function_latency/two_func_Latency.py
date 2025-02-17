#!/usr/bin/python
# @lint-avoid-python-3-compatibility-imports
#
# funclatency   Time functions and print latency as a histogram.
#               For Linux, uses BCC, eBPF.
#
# USAGE: funclatency [-h] [-p PID] [-i INTERVAL] [-T] [-u] [-m] [-F] [-r] [-v]
#                    pattern
#
# Run "funclatency -h" for full usage.
#
# The pattern is a string with optional '*' wildcards, similar to file
# globbing. If you'd prefer to use regular expressions, use the -r option.
#
# Currently nested or recursive functions are not supported properly, and
# timestamps will be overwritten, creating dubious output. Try to match single
# functions, or groups of functions that run at the same stack layer, and
# don't ultimately call each other.
#
# Copyright (c) 2015 Brendan Gregg.
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 15-Mar-2019   Nizar El Zarif      Created this.

from __future__ import print_function
from bcc import BPF
from time import sleep, strftime
import argparse
import signal

# arguments
examples = """examples:
    ./two_func_latency.py -A tcp_recvmsg -B __napi_schedule
"""
parser = argparse.ArgumentParser(
    description="Time between calling the first functions and the return of the second",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("-A",
    help="The first function")
parser.add_argument("-B",
    help="Second function")
parser.add_argument("-p", "--pid", type=int,
    help="trace this PID only")
parser.add_argument("-i", "--interval", type=int,
    help="summary interval, in seconds")
parser.add_argument("-d", "--duration", type=int,
    help="total duration of trace, in seconds")
parser.add_argument("-T", "--timestamp", action="store_true",
    help="include timestamp on output")
parser.add_argument("-u", "--microseconds", action="store_true",
    help="microsecond histogram")
parser.add_argument("-m", "--milliseconds", action="store_true",
    help="millisecond histogram")
parser.add_argument("-F", "--function", action="store_true",
    help="show a separate histogram per function")
parser.add_argument("-r", "--regexp", action="store_true",
    help="use regular expressions. Default is \"*\" wildcards only.")
parser.add_argument("-v", "--verbose", action="store_true",
    help="print the BPF program (for debugging purposes)")
parser.add_argument("--ebpf", action="store_true",
    help=argparse.SUPPRESS)
args = parser.parse_args()
if args.duration and not args.interval:
    args.interval = args.duration
if not args.interval:
    args.interval = 99999999

def bail(error):
    print("Error: " + error)
    exit(1)

parts = args.A.split(':')
if len(parts) == 1:
    library = None
    pattern_A = args.A
elif len(parts) == 2:
    library = parts[0]
    libpath = BPF.find_library(library) or BPF.find_exe(library)
    if not libpath:
        bail("can't resolve library %s" % library)
    library = libpath
    pattern_A = parts[1]
else:
    bail("unrecognized pattern_A format '%s'" % pattern)

if not args.regexp:
    pattern_A = pattern_A.replace('*', '.*')
    pattern_A = '^' + pattern_A + '$'

parts = args.B.split(':')
if len(parts) == 1:
    library = None
    pattern_B = args.B
elif len(parts) == 2:
    library = parts[0]
    libpath = BPF.find_library(library) or BPF.find_exe(library)
    if not libpath:
        bail("can't resolve library %s" % library)
    library = libpath
    pattern_B = parts[1]
else:
    bail("unrecognized pattern_B format '%s'" % pattern_B)

if not args.regexp:
    pattern_B = pattern_B.replace('*', '.*')
    pattern_B = '^' + pattern_B + '$'

# define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>

typedef struct ip_pid {
    u64 ip;
    u64 pid;
} ip_pid_t;

typedef struct hist_key {
    ip_pid_t key;
    u64 slot;
} hist_key_t;

BPF_HASH(start, u32);
STORAGE

int trace_func_entry(struct pt_regs *ctx)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid;
    u32 tgid = pid_tgid >> 32;
    u64 ts = bpf_ktime_get_ns();
    //bpf_trace_printk("%d,1\\n",ts);
    FILTER
    ENTRYSTORE
    start.update(&pid, &ts);

    return 0;
}

int trace_func_return(struct pt_regs *ctx)
{
    u64 *tsp, delta, now;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid;
    u32 tgid = pid_tgid >> 32;

    // calculate delta time
    tsp = start.lookup(&pid);
    if (tsp == 0) {
        return 0;   // missed start
    }
    now = bpf_ktime_get_ns();
    bpf_trace_printk("%d,2\\n",now);
    start.delete(&pid);
    FACTOR

    // store as histogram
    STORE

    return 0;
}
"""

# do we need to store the IP and pid for each invocation?
need_key = args.function or (library and not args.pid)

# code substitutions
if args.pid:
    bpf_text = bpf_text.replace('FILTER',
        'if (tgid != %d) { return 0; }' % args.pid)
else:
    bpf_text = bpf_text.replace('FILTER', '')
if args.milliseconds:
    bpf_text = bpf_text.replace('FACTOR', 'delta /= 1000000;')
    label = "msecs"
elif args.microseconds:
    bpf_text = bpf_text.replace('FACTOR', 'delta /= 1000;')
    label = "usecs"
else:
    bpf_text = bpf_text.replace('FACTOR', '')
    label = "nsecs"
if need_key:
    bpf_text = bpf_text.replace('STORAGE', 'BPF_HASH(ipaddr, u32);\n' +
        'BPF_HISTOGRAM(dist, hist_key_t);')
    # stash the IP on entry, as on return it's kretprobe_trampoline:
    bpf_text = bpf_text.replace('ENTRYSTORE',
        'u64 ip = PT_REGS_IP(ctx); ipaddr.update(&pid, &ip);')
    pid = '-1' if not library else 'tgid'
    bpf_text = bpf_text.replace('STORE',
        """
    u64 ip, *ipp = ipaddr.lookup(&pid);
    if (ipp) {
        ip = *ipp;
        hist_key_t key;
        key.key.ip = ip;
        key.key.pid = %s;
        key.slot = bpf_log2l(delta);
        dist.increment(key);
        ipaddr.delete(&pid);
    }
        """ % pid)
else:
    bpf_text = bpf_text.replace('STORAGE', 'BPF_HISTOGRAM(dist);')
    bpf_text = bpf_text.replace('ENTRYSTORE', '')
    bpf_text = bpf_text.replace('STORE',
        'dist.increment(bpf_log2l(delta));')
if args.verbose or args.ebpf:
    print(bpf_text)
    if args.ebpf:
        exit()

# signal handler
def signal_ignore(signal, frame):
    print()

# load BPF program
b = BPF(text=bpf_text)
print(pattern_A + " " + pattern_B)
# attach probes
if not library:
    b.attach_kprobe(event_re=pattern_A, fn_name="trace_func_entry")
    b.attach_kretprobe(event_re=pattern_B, fn_name="trace_func_return")
    matched = b.num_open_kprobes()
else:
    b.attach_uprobe(name=library, sym_re=pattern_A, fn_name="trace_func_entry",
                    pid=args.pid or -1)
    b.attach_uretprobe(name=library, sym_re=pattern_B,
                       fn_name="trace_func_return", pid=args.pid or -1)
    matched = b.num_open_uprobes()

if matched == 0:
    print("0 functions matched by \"%s\". Exiting." % args.B)
    exit()

# header
print("Tracing %d functions for \"%s\"... Hit Ctrl-C to end." %
    (matched / 2, args.B))

# output
def print_section(key):
    if not library:
        return BPF.sym(key[0], -1)
    else:
        return "%s [%d]" % (BPF.sym(key[0], key[1]), key[1])

exiting = 0 if args.interval else 1
seconds = 0
dist = b.get_table("dist")
while (1):
    try:
        print(b.trace_print())
        sleep(args.interval)
        seconds += args.interval
    except KeyboardInterrupt:
        exiting = 1
        # as cleanup can take many seconds, trap Ctrl-C:
        signal.signal(signal.SIGINT, signal_ignore)
    if args.duration and seconds >= args.duration:
        exiting = 1

    print()
    if args.timestamp:
        print("%-8s\n" % strftime("%H:%M:%S"), end="")

    if need_key:
        dist.print_log2_hist(label, "Function", section_print_fn=print_section,
            bucket_fn=lambda k: (k.ip, k.pid))
    else:
        dist.print_log2_hist(label)
    dist.clear()

    if exiting:
        print("Detaching...")
        exit()
