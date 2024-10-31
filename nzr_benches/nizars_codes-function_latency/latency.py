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
# 20-Sep-2015   Brendan Gregg       Created this.
# 06-Oct-2016   Sasha Goldshtein    Added user function support.
# 18-Mar-3019   Nizar EL Zarif	    Added secibd function tracing and output to CSV
from __future__ import print_function
from bcc import BPF
from time import sleep, strftime
import argparse
import signal
import csv
# arguments
examples = """examples:
    ./funclatency do_sys_open       # time the do_sys_open() kernel function
    ./funclatency c:read            # time the read() C library function
    ./funclatency -u vfs_read       # time vfs_read(), in microseconds
    ./funclatency -m do_nanosleep   # time do_nanosleep(), in milliseconds
    ./funclatency -i 2 -d 10 c:open # output every 2 seconds, for duration 10s
    ./funclatency -mTi 5 vfs_read   # output every 5 seconds, with timestamps
    ./funclatency -p 181 vfs_read   # time process 181 only
    ./funclatency 'vfs_fstat*'      # time both vfs_fstat() and vfs_fstatat()
    ./funclatency 'c:*printf'       # time the *printf family of functions
    ./funclatency -F 'vfs_r*'       # show one histogram per matched function
"""
parser = argparse.ArgumentParser(
    description="Time functions and print latency as a histogram",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
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
parser.add_argument("-S",
    help="we can track two functions at the same time")
parser.add_argument("pattern",
    help="search expression for functions")
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
# Library where the function may be added like lib:function
parts = args.pattern.split(':')
if len(parts) == 1:
    library = None
    pattern = args.pattern
elif len(parts) == 2:
    library = parts[0]
    libpath = BPF.find_library(library) or BPF.find_exe(library)
    if not libpath:
        bail("can't resolve library %s" % library)
    library = libpath
    pattern = parts[1]
else:
    bail("unrecognized pattern format '%s'" % pattern)

if not args.regexp:
    pattern = pattern.replace('*', '.*')
    pattern = '^' + pattern + '$'

parts = args.S.split(':')
if len(parts) == 1:
    second_library = None
    second_pattern = args.S
elif len(parts) == 2:
    second_library = parts[0]
    libpath = BPF.find_library(second_library) or BPF.find_exe(second_library)
    if not libpath:
        bail("can't resolve library %s" % second_library)
    second_library = libpath
    second_pattern = parts[1]
else:
    bail("unrecognized pattern format '%s'" % pattern)

if not args.regexp:
    second_pattern = second_pattern.replace('*', '.*')
    second_pattern = '^' + second_pattern + '$'

# define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

// define output data structure in C
struct data_t {
    u32 pid;
    u64 ts;
    char comm[TASK_COMM_LEN];
    u32 nb;
};
BPF_PERF_OUTPUT(events);

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
    

    struct data_t data = {};
    data.pid = pid;
    data.ts = ts;
    data.nb = 1;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    events.perf_submit(ctx, &data, sizeof(data)); 
    FILTER
    ENTRYSTORE
    start.update(&pid, &ts);
    return 0;
}

int trace_func_return(struct pt_regs *ctx)
{
    u64 *tsp, delta;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid;
    u32 tgid = pid_tgid >> 32;
    
    struct data_t data2 = {};

    // calculate delta time
    tsp = start.lookup(&pid);
    if (tsp == 0) {
        return 0;   // missed start
    }
    delta = bpf_ktime_get_ns() - *tsp;
    data2.ts = bpf_ktime_get_ns();
    data2.pid = pid;
    data2.nb = 2;
    bpf_get_current_comm(&data2.comm, sizeof(data2.comm));
    start.delete(&pid);
    FACTOR
    events.perf_submit(ctx, &data2, sizeof(data2));

    // store as histogram
    // STORE
    return 0;
}

int trace_second_func_entry(struct pt_regs *ctx)
{
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid;
    u32 tgid = pid_tgid >> 32;
    u64 ts = bpf_ktime_get_ns();


    struct data_t data = {};
    data.pid = pid;
    data.ts = ts;
    data.nb = 3;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    events.perf_submit(ctx, &data, sizeof(data));
    FILTER
    ENTRYSTORE
    start.update(&pid, &ts);
    return 0;
}

int trace_second_func_return(struct pt_regs *ctx)
{
    u64 *tsp, delta;
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid;
    u32 tgid = pid_tgid >> 32;

    struct data_t data2 = {};

    // calculate delta time
    tsp = start.lookup(&pid);
    if (tsp == 0) {
        return 0;   // missed start
    }
    delta = bpf_ktime_get_ns() - *tsp;
    data2.ts = bpf_ktime_get_ns();
    data2.pid = pid;
    data2.nb = 4;
    bpf_get_current_comm(&data2.comm, sizeof(data2.comm));
    start.delete(&pid);
    FACTOR
    events.perf_submit(ctx, &data2, sizeof(data2));

    // store as histogram
    // STORE
    return 0;
}

"""

# do we need to store the IP and pid for each invocation?
need_key = args.function or (library and not args.pid)
# header
print("%-18s %-16s %-6s %s" % ("TIME(s)", "COMM", "PID", "MESSAGE"))
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

# attach probes
if not library:
    b.attach_kprobe(event_re=pattern, fn_name="trace_func_entry")
    b.attach_kretprobe(event_re=pattern, fn_name="trace_func_return")
    b.attach_kprobe(event_re=second_pattern, fn_name="trace_second_func_entry")
    b.attach_kretprobe(event_re=second_pattern, fn_name="trace_second_func_return")
    matched = b.num_open_kprobes()
else:
    b.attach_uprobe(name=library, sym_re=pattern, fn_name="trace_func_entry",
                    pid=args.pid or -1)
    b.attach_uretprobe(name=library, sym_re=pattern,
                       fn_name="trace_second_func_return", pid=args.pid or -1)
    b.attach_uprobe(name=second_library, sym_re=second_pattern, fn_name="trace_func_entry",
                    pid=args.pid or -1)
    b.attach_uretprobe(name=second_library, sym_re=second_pattern,
                       fn_name="trace_second_func_return", pid=args.pid or -1)
    matched = b.num_open_uprobes()

if matched == 0:
    print("0 functions matched by \"%s\". Exiting." % args.pattern)
    exit()

# header
print("Tracing %d functions for \"%s\"... Hit Ctrl-C to end." %
    (matched / 2, args.pattern))

# output
def print_section(key):
    if not library:
        return BPF.sym(key[0], -1)
    else:
        return "%s [%d]" % (BPF.sym(key[0], key[1]), key[1])


out_csv = open('output.csv', 'w')

with out_csv:
	writer =csv.writer(out_csv ,delimiter=',');
	writer.writerow(['Timestamp','function_name','PID','kprobe_nb'])
	

start = 0
def print_event(cpu, data, size):
    global start
    event = b["events"].event(data)
    if start == 0:
            start = event.ts
    time_s = (float(event.ts - start)) / 1000000000
    print("%-18.9f %-16s %-6d %s" % (time_s, event.comm, event.pid, event.nb 
        ))
    if event.nb == 1:
	which_probe='function_1_entry'
    elif event.nb == 2:
        which_probe='function_1_return'
    elif event.nb == 3:
        which_probe='function_2_entry'
    elif event.nb == 4:
        which_probe='function_2_return'	
    out_csv = open('output.csv', 'a')
    with out_csv:
        writer =csv.writer(out_csv,delimiter=',');
        writer.writerow([time_s, event.comm, event.pid, which_probe])

exiting = 0 if args.interval else 1
seconds = 0
dist = b.get_table("dist")
# loop with callback to print_event
b["events"].open_perf_buffer(print_event)
while (1):
    try:
        b.perf_buffer_poll()
	#sleep(args.interval)
        seconds += args.interval
    except KeyboardInterrupt:
        exiting = 1
        # as cleanup can take many seconds, trap Ctrl-C:
        signal.signal(signal.SIGINT, signal_ignore)
        exit()
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
