#!/usr/bin/env python3
#
# SPDX-license-identifier: Apache-2.0
#
# rt-trace.py: A bcc-based tool for tracing RT tasks.
#
# Authors: Peter Xu <peterx@redhat.com>
#
# Usage:
#   $ sudo ./rt-trace.py --cpu-list <isolcpus_list>
# Example:
#   $ sudo ./rt-trace.py --cpu-list 1,3,5,15-20
#
# Normally --cpu-list should be the isolcpus or subset of it on the RT system.
# For more help, try --help.
#
# Hooks to observe on isolcpus:
# - kprobes
#   - smp_apic_timer_interrupt/__sysvec_apic_timer_interrupt
#   - process_one_work, dump work item
# - tracepoints
#   - sched_switch
#   - sys_enter_clock_nanosleep
#   - sys_exit_clock_nanosleep
#
# Hooks to observe when the target is within isolcpus list (kprobes):
# - __queue_work, __queue_delayed_work (covers queue_work_on, etc.)
# - smp_call_function
# - smp_call_function_any
# - smp_call_function_many_cond (covers on_each_cpu_cond_mask, smp_call_function_many)
# - generic_exec_single (covers smp_call_function_single, smp_call_function_single_async)
#
# TODO:
# - Support MAX_N_CPUS to 256 cores, maybe?  Currently it's 64.

from bcc import BPF
import argparse
import signal
import ctypes
import sys
import os

VERSION = "0.1.2"

# Limit this because we use one u64 as cpumask.  Problem is BPF does not allow
# loop, so any real cpumask won't work.
MAX_N_CPUS = 64

#
# Global vars
#
# To be generated, as part of BPF program
hooks = ""
# Keeps a list of hooks that are enabled
hook_active_list = []
# List of cpus to trace
cpu_list = []
# BPF program pointer, etc.
bpf = None
stack_traces = None
args = None

def err(out):
    print("ERROR: " + out)
    exit(-1)

def parse_cpu_list(cpu_list):
    out = []
    def check_index(n):
        if n >= MAX_N_CPUS:
            err("CPU index overflow (%s>=%s)" % (n, MAX_N_CPUS))
    subsets = cpu_list.split(",")
    for subset in subsets:
        if "-" in subset:
            start, end = subset.split("-")
            start = int(start)
            end = int(end)
            if start >= end:
                err("Illegal range specified: %s-%s", (start, end))
            check_index(end)
            for i in range(int(start), int(end) + 1):
                out.append(i)
            continue
        else:
            cpu = int(subset)
            check_index(cpu)
            out.append(cpu)
    return out

def parse_args():
    global cpu_list, args
    parser = argparse.ArgumentParser(
        description='Bcc-based trace tool for Real-Time workload.')
    parser.add_argument("--cpu-list", "-c",
                        help='Cores to trace interruptions (e.g., 1,2-5,8)')
    parser.add_argument("--backtrace", "-b", action='store_true',
                        help='Whether dump backtrace when possible (default: off)')
    parser.add_argument("--debug", "-d", action='store_true',
                        help='Whether run with debug mode (default: off)')
    parser.add_argument("--version", "-v", action='store_true',
                        help='Dump version information (current: %s)' % VERSION)
    args = parser.parse_args()
    if args.version:
        print("Version: %s" % VERSION)
        exit(0)
    if not args.cpu_list:
        print("CPU list (--cpu-list/-c) is required.  " +
              "Please use '-h' to dump the complete help message.")
        exit(0)
    cpu_list = parse_cpu_list(args.cpu_list)
    try:
        cpu_list = parse_cpu_list(args.cpu_list)
    except:
        err("Invalid cpu list: %s" % args.cpu_list)

parse_args()

#
# To enable one tracepoint/kprobe, change "enabled" to True.
#
tracepoint_list = {
    "sched_switch": {
        "enabled": False,
        "tracepoint": "sched:sched_switch",
    },
    "clock_nanosleep_enter": {
        "enabled": False,
        "tracepoint": "syscalls:sys_enter_clock_nanosleep"
    },
    "clock_nanosleep_exit": {
        "enabled": False,
        "tracepoint": "syscalls:sys_exit_clock_nanosleep",
    },
}

#
# These are the types of hooks:
#
# Trace anything happened on the local/specific core
KPROBE_T_TRACE_LOCAL                = 0
# Trace only if the core matches the first argument of the kprobe
KPROBE_T_FIRST_INT_MATCH            = 1
# Trace only if the first arg (which is a cpumask) contains the cpu specified
# FIXME: current this is broken, try enable any of the hook with it
KPROBE_T_FIRST_CPUMASK_CONTAINS     = 2

#
# List of kprobes.  Type is defined as KPROBE_T_*.  When "kprobe" is defined,
# use that for attach_kprobe(), otherwise use the key as "kprobe".
#
dynamic_kprobe_list = {
    "__queue_work": {
        "enabled": True,
        "subtype": KPROBE_T_FIRST_INT_MATCH,
    },
    "__queue_delayed_work": {
        "enabled": True,
        "subtype": KPROBE_T_FIRST_INT_MATCH,
    },
    "smp_call_function": {
        "enabled": True,
        "subtype": KPROBE_T_TRACE_LOCAL,
    },
    "smp_call_function_any": {
        "enabled": True,
        "subtype": KPROBE_T_TRACE_LOCAL,
    },
    "smp_call_function_many_cond": {
        # Includes "on_each_cpu", "on_each_cpu_cond_mask",
        # "smp_call_function_many", "on_each_cpu_cond_mask"
        "enabled": True,
        "subtype": KPROBE_T_FIRST_CPUMASK_CONTAINS,
    },
    "generic_exec_single": {
        # Includes "smp_call_function_single", "smp_call_function_single_async"
        "enabled": True,
        "subtype": KPROBE_T_FIRST_INT_MATCH,
    },
    # This does not work on some kernels; temporarily remove it.
    # "apic_timer_interrupt": {
    #     "enabled": False,
    #     "subtype": KPROBE_T_TRACE_LOCAL,
    #     # smp_apic_timer_interrupt/__sysvec_apic_timer_interrupt
    #     "kprobe": list(BPF.get_kprobe_functions(
    #         b".*apic_timer_interrupt"))[0].decode()
    # }
}

def handle_process_one_work(name, event):
    return "%s (func=%s)" % (name, bpf.ksym(event.arg1).decode('utf-8'))

# These kprobes have custom hooks so they can dump more things
static_kprobe_list = {
    "process_one_work": {
        "enabled": True,
        "handler": handle_process_one_work,
    }
}

# Main body of the BPF program
body = """
#include <linux/sched.h>
#include <linux/cpumask.h>
#include <linux/workqueue.h>

struct data_t {
    u32 msg_type;
    u32 pid;
    u64 ts;
    // for MSG_TYPE_PROCESS_ONE_WORK, it's pointer to a work_func_t.
    u64 arg1;
    char comm[TASK_COMM_LEN];
    u32 cpu;
#if BACKTRACE_ENABLED
    u32 stack_id;
#endif
};

// Used to communicate with the userspace program
BPF_PERF_OUTPUT(events);
// Cpumask of which trace is enabled.  Now only covers 64 cores.
BPF_ARRAY(trace_enabled, u64, 1);

#if BACKTRACE_ENABLED
// Calltrace buffers
BPF_STACK_TRACE(stack_traces, 1024);
#endif

static inline void
fill_data(struct data_t *data, u32 msg_type)
{
    data->msg_type = msg_type;
    data->pid = bpf_get_current_pid_tgid();
    data->ts = bpf_ktime_get_ns();
    data->cpu = bpf_get_smp_processor_id();
#if BACKTRACE_ENABLED
    // stack_id can be -EFAULT (0xfffffff2) when not applicable
    data->stack_id = stack_traces.get_stackid(ctx, 0);
#endif
    bpf_get_current_comm(data->comm, sizeof(data->comm));
}

// Base function to be called by all kinds of hooks
static inline void
kprobe_common(struct pt_regs *ctx, u32 msg_type)
{
    struct data_t data = {};
    fill_data(&data, msg_type);
    events.perf_submit(ctx, &data, sizeof(data));
}

static inline u64* get_cpu_list(void)
{
    int index = 0;

    return trace_enabled.lookup(&index);
}

static inline bool cpu_in_trace_list(void)
{
    int cpu = bpf_get_smp_processor_id();
    u64 *cpu_list = get_cpu_list();

    if (cpu >= MAX_N_CPUS || !cpu_list)
        return false;

    if ((1UL << cpu) & *cpu_list)
        return true;

    return false;
}

// Submit message as long as the core has enabled tracing
static inline void
kprobe_trace_local(struct pt_regs *ctx, u32 msg_type)
{
    if (cpu_in_trace_list())
        kprobe_common(ctx, msg_type);
}

#if ENABLE_PROCESS_ONE_WORK
// constant hook on process_one_work
int kprobe__process_one_work(struct pt_regs *regs, void *worker,
                             struct work_struct *work)
{
    struct data_t data = {};

    if (!cpu_in_trace_list())
        return 0;

    fill_data(&data, MSG_TYPE_PROCESS_ONE_WORK);
    data.arg1 = (u64)work->func;
    events.perf_submit(regs, &data, sizeof(data));
    return 0;
}
#endif

// Submit only if the specified cpu is in the tracing cpu list
static inline void
kprobe_first_arg_match(struct pt_regs *ctx, int cpu, u32 msg_type)
{
    u64 *cpu_list = get_cpu_list();
    
    if (cpu >= MAX_N_CPUS || !cpu_list)
        return;

    if ((1UL << cpu) & *cpu_list)
        kprobe_common(ctx, msg_type);
}

// Submit only if any specified cpu is in the cpumask
static inline void
kprobe_first_cpumask_contains(struct pt_regs *ctx, struct cpumask *mask,
                              u32 msg_type)
{
    u64 *cpu_list = get_cpu_list(), *ptr = (u64 *)mask;

    if (!cpu_list || !ptr)
        return;

    if (*cpu_list & *ptr)
        kprobe_common(ctx, msg_type);
}

GENERATED_HOOKS
"""

# Allow quitting the tracing using Ctrl-C
def int_handler(signum, frame):
    exit(0)
signal.signal(signal.SIGINT, int_handler)

def hook_name(name):
    """Return function name of a hook point to attach"""
    return "func____" + name

def hook_append(name, _type, _sub_type=KPROBE_T_TRACE_LOCAL):
    """Enable a hook with type, by appending the BPF program.  When `_type'
    is 'kprobe', need to provide subtype."""
    global hooks, hook_active_list
    # Fetch the next index to use
    index = len(hook_active_list)
    if _type == "tp" or _sub_type == KPROBE_T_TRACE_LOCAL:
        # For either tracepoints or trace-local kprobes, trace all thing
        # happened on specific cores
        hooks += """
int %s(struct pt_regs *ctx)
{
    kprobe_trace_local(ctx, %d);
    return 0;
}
""" % (hook_name(name), index)
    elif _sub_type == KPROBE_T_FIRST_INT_MATCH:
        hooks += """
int %s(struct pt_regs *ctx, int cpu)
{
    kprobe_first_arg_match(ctx, cpu, %d);
    return 0;
}
""" % (hook_name(name), index)
    elif _sub_type == KPROBE_T_FIRST_CPUMASK_CONTAINS:
        hooks += """
int %s(struct pt_regs *ctx, struct cpumask *mask)
{
    kprobe_first_cpumask_contains(ctx, mask, %d);
    return 0;
}
""" % (hook_name(name), index)
    else:
        err("Unknown type")
    # Create mapping in hook_active_list
    hook_active_list.append({
        "type": _type,
        "name": name,
    })

def print_event(cpu, data, size):
    global bpf, stack_traces, args

    event = bpf["events"].event(data)
    time_s = (float(event.ts)) / 1000000000
    entry = hook_active_list[event.msg_type]
    name = entry["name"]
    if entry["type"] == "static_kprobe":
        static_entry = static_kprobe_list[name]
        msg = static_entry["handler"](name, event)
    else:
        msg = name
    print("%-18.9f %-20s %-4d %-8d %s" %
          (time_s, event.comm.decode("utf-8"), event.cpu, event.pid, msg))

    if args.backtrace:
        stack_id = event.stack_id
        # Skip for -EFAULT
        if stack_id != 0xfffffff2:
            for addr in stack_traces.walk(stack_id):
                sym = bpf.ksym(addr, show_offset=True).decode("utf-8")
                print("\t%s" % sym)

def apply_cpu_list(bpf, cpu_list):
    """Apply the cpu_list to BPF program"""
    cpu_array = bpf.get_table("trace_enabled")
    out = 0
    for cpu in cpu_list:
        out |= 1 << cpu
    cpu_array[0] = ctypes.c_uint64(out)

def main():
    global bpf, stack_traces, cpu_list, body

    # Enable enabled tracepoints
    for name, entry in tracepoint_list.items():
        if not entry["enabled"]:
            continue
        hook_append(name, _type="tp")
    for name, entry in dynamic_kprobe_list.items():
        if not entry["enabled"]:
            continue
        hook_append(name, _type="kprobe", _sub_type=entry["subtype"])
    for name, entry in static_kprobe_list.items():
        index = len(hook_active_list)
        enable = "ENABLE_" + name.upper()
        msg_type = "MSG_TYPE_" + name.upper()
        body = body.replace(enable, "%d" % entry["enabled"])
        if not entry["enabled"]:
            continue
        body = body.replace(msg_type, "%d" % index)
        hook_active_list.append({
            "name": name,
            "type": "static_kprobe",
        })

    body = body.replace("GENERATED_HOOKS", hooks)
    body = body.replace("BACKTRACE_ENABLED", "1" if args.backtrace else "0")
    body = body.replace("MAX_N_CPUS", "%d" % MAX_N_CPUS)
    if args.debug:
        print(body)
        exit(0)
    bpf = BPF(text=body)

    for entry in hook_active_list:
        name = entry["name"]
        t = entry["type"]
        if t == "tp":
            entry = tracepoint_list[name]
            bpf.attach_tracepoint(tp=entry["tracepoint"], fn_name=hook_name(name))
        elif t == "kprobe":
            entry = dynamic_kprobe_list[name]
            if "kprobe" in entry:
                kprobe = entry["kprobe"]
            else:
                kprobe = name
            bpf.attach_kprobe(event=kprobe, fn_name=hook_name(name))
        print("Enabled hook point: %s" % name)

    if args.backtrace:
        stack_traces = bpf.get_table("stack_traces")
    apply_cpu_list(bpf, cpu_list)

    print("%-18s %-20s %-4s %-8s %s" % ("TIME(s)", "COMM", "CPU", "PID", "MSG"))
    bpf["events"].open_perf_buffer(print_event)
    while 1:
        bpf.perf_buffer_poll()

main()
