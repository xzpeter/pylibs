#!/usr/bin/env python
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
#   - irq_work_queue (queue work locally)
#   - smp_apic_timer_interrupt/__sysvec_apic_timer_interrupt
# - tracepoints
#   - sched_switch
#   - sys_enter_clock_nanosleep
#   - sys_exit_clock_nanosleep
#
# Hooks to observe when the target is within isolcpus list (kprobes):
# - queue_work_on
# - smp_call_function
# - smp_call_function_any
# - smp_call_function_many
# - smp_call_function_many_cond
# - smp_call_function_single
# - smp_call_function_single_async
# - irq_work_queue_on
# - on_each_cpu_cond_mask

from bcc import BPF
import argparse
import signal
import ctypes
import sys

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
kprobe_list = {
    "queue_work_on": {
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
        # Includes "smp_call_function_many"
        "enabled": True,
        "subtype": KPROBE_T_FIRST_CPUMASK_CONTAINS,
    },
    "generic_exec_single": {
        # Includes "smp_call_function_single", "smp_call_function_single_async"
        "enabled": True,
        "subtype": KPROBE_T_FIRST_INT_MATCH,
    },
    "irq_work_queue_on": {
        "enabled": False,
        "subtype": KPROBE_T_TRACE_LOCAL,
    },
    "on_each_cpu_cond_mask": {
        "enabled": False,
        "subtype": KPROBE_T_TRACE_LOCAL,
    },
    "apic_timer_interrupt": {
        "enabled": False,
        "subtype": KPROBE_T_TRACE_LOCAL,
        # smp_apic_timer_interrupt/__sysvec_apic_timer_interrupt
        "kprobe": list(BPF.get_kprobe_functions(
            b".*apic_timer_interrupt"))[0].decode()
    }
}

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
MAX_N_CPUS = 1024

def parse_cpu_list(cpu_list):
    out = []
    def check_index(n):
        if n >= MAX_N_CPUS:
            err("CPU index overflow (%s>%s)" % (n, MAX_N_CPUS))
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
    parser = argparse.ArgumentParser(description='Trace tool for Real-Time workload.')
    parser.add_argument("--cpu-list", "-c", required=True,
                        help='Cores to trace interruptions (e.g., 1,2-5,8)')
    parser.add_argument("--backtrace", "-b", action='store_true',
                        help='Whether dump backtrace when possible (default: off)')
    parser.add_argument("--debug", "-d", action='store_true',
                        help='Whether run with debug mode (default: off)')
    args = parser.parse_args()
    try:
        cpu_list = parse_cpu_list(args.cpu_list)
    except:
        err("Invalid cpu list: %s" % args.cpu_list)

parse_args()

# Main body of the BPF program
body = """
#include <linux/sched.h>
#include <linux/cpumask.h>

struct data_t {
    u64 ts;
    char comm[TASK_COMM_LEN];
    u32 msg_type;
    u32 pid;
    u32 stack_id;
    u32 cpu;
};
// Used to communicate with the userspace program
BPF_PERF_OUTPUT(events);
// Calltrace buffers
BPF_STACK_TRACE(stack_traces, 1024);
// Whether trace enabled on this cpu
BPF_ARRAY(trace_enabled, u64, %s);

// Base function to be called by all kinds of hooks
static inline void
kprobe_common(struct pt_regs *ctx, u32 msg_type)
{
    struct data_t data = {};
    u32 cpu = bpf_get_smp_processor_id();

    data.msg_type = msg_type;
    data.pid = bpf_get_current_pid_tgid();
    data.ts = bpf_ktime_get_ns();
    data.cpu = cpu;
    if (%d) {
        // stack_id can be -EFAULT (0xfffffff2) when not applicable
        data.stack_id = stack_traces.get_stackid(ctx, 0);
    }
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    events.perf_submit(ctx, &data, sizeof(data));
}

// Submit message as long as the core has enabled tracing
static inline void
kprobe_trace_local(struct pt_regs *ctx, u32 msg_type)
{
    u32 cpu = bpf_get_smp_processor_id();
    u64 *enabled = trace_enabled.lookup(&cpu);

    if (!enabled || !*enabled)
        return;

    kprobe_common(ctx, msg_type);
}

// Submit only if the specified cpu is in the tracing cpu list
static inline void
kprobe_first_arg_match(struct pt_regs *ctx, int cpu, u32 msg_type)
{
    u64 *enabled = trace_enabled.lookup(&cpu);
    
    if (!enabled || !*enabled)
        return;

    kprobe_common(ctx, msg_type);
}

// Submit only if any specified cpu is in the cpumask
static inline void
kprobe_first_cpumask_contains(struct pt_regs *ctx, struct cpumask *mask,
                              u32 msg_type)
{
    int cpu, trace_this = 0;
    u64 *enabled;

    // TODO: This may be less efficient than a cpumask intersection, but we
    // need to know how to interface a cpumask between Python and bpf..
    for_each_cpu(cpu, mask) {
        enabled = trace_enabled.lookup(&cpu);
        if (enabled && *enabled) {
            trace_this = 1;
            break;
        }
    }

    if (trace_this) {
        kprobe_common(ctx, msg_type);
    }
}
""" % (MAX_N_CPUS, args.backtrace)

# Allow quitting the tracing using Ctrl-C
def int_handler(signum, frame):
    exit(0)
signal.signal(signal.SIGINT, int_handler)

def err(out):
    print("ERROR: " + out)
    exit(-1)

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
    name = hook_active_list[event.msg_type]["name"]
    print("%-18.9f %-20s %-4d %-8d %s" %
          (time_s, event.comm.decode("utf-8"), event.cpu, event.pid, name))

    if args.backtrace:
        stack_id = event.stack_id
        # Skip for -EFAULT
        if stack_id != 0xfffffff2:
            for addr in stack_traces.walk(stack_id):
                sym = bpf.ksym(addr, show_offset=True)
                print("\t%s" % sym)

def main():
    global bpf, stack_traces, cpu_list

    # Enable enabled tracepoints
    for name, entry in tracepoint_list.items():
        if not entry["enabled"]:
            continue
        hook_append(name, _type="tp")
    for name, entry in kprobe_list.items():
        if not entry["enabled"]:
            continue
        hook_append(name, _type="kprobe", _sub_type=entry["subtype"])
    full = body + hooks
    if args.debug:
        print(full)
        exit(0)
    bpf = BPF(text=full)

    for entry in hook_active_list:
        name = entry["name"]
        t = entry["type"]
        if t == "tp":
            entry = tracepoint_list[name]
            bpf.attach_tracepoint(tp=entry["tracepoint"], fn_name=hook_name(name))
        elif t == "kprobe":
            entry = kprobe_list[name]
            if "kprobe" in entry:
                kprobe = entry["kprobe"]
            else:
                kprobe = name
            bpf.attach_kprobe(event=kprobe, fn_name=hook_name(name))
        print("Enabled hook point: %s" % name)

    stack_traces = bpf.get_table("stack_traces")
    cpu_array = bpf.get_table("trace_enabled")
    for cpu in cpu_list:
        cpu_array[cpu] = ctypes.c_uint64(1)

    print("%-18s %-20s %-4s %-8s %s" % ("TIME(s)", "COMM", "CPU", "PID", "TYPE"))
    bpf["events"].open_perf_buffer(print_event)
    while 1:
        bpf.perf_buffer_poll()

main()