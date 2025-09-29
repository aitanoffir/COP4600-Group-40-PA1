#!/usr/bin/env python3
"""
scheduler-gpt.py

Usage:
    python3 scheduler-gpt.py inputfile.in

Produces:
    inputfile.out
"""
import sys
import os
from collections import deque

class Process:
    def __init__(self, name, arrival, burst, index):
        self.name = name
        self.arrival = int(arrival)
        self.burst = int(burst)
        self.remaining = int(burst)
        self.start_time = None   # first time scheduled
        self.finish_time = None
        self.index = index       # input order tie-break

def error_and_exit(msg):
    print(msg)
    sys.exit(1)

def usage_and_exit():
    print("Usage: scheduler-gpt.py <input file>")
    sys.exit(1)

def parse_input_file(filename):
    if not os.path.exists(filename):
        usage_and_exit()

    with open(filename, 'r') as f:
        raw = f.readlines()

    # strip comments and blanks
    lines = []
    for ln in raw:
        if '#' in ln:
            ln = ln.split('#', 1)[0]
        ln = ln.strip()
        if ln:
            lines.append(ln)

    params = {}
    processes = []
    idx = 0
    proc_index = 0
    while idx < len(lines):
        parts = lines[idx].split()
        key = parts[0].lower()
        if key == 'processcount':
            if len(parts) < 2:
                error_and_exit("Error: Missing parameter processcount")
            params['processcount'] = int(parts[1])
        elif key == 'runfor':
            if len(parts) < 2:
                error_and_exit("Error: Missing parameter runfor")
            params['runfor'] = int(parts[1])
        elif key == 'use':
            if len(parts) < 2:
                error_and_exit("Error: Missing parameter use")
            params['use'] = parts[1].lower()
        elif key == 'quantum':
            if len(parts) < 2:
                error_and_exit("Error: Missing parameter quantum")
            try:
                params['quantum'] = int(parts[1])
            except:
                error_and_exit("Error: Missing parameter quantum")
        elif key == 'process':
            # parse tokens: process name <NAME> arrival <A> burst <B>
            tokens = parts[1:]
            kv = {}
            i = 0
            while i < len(tokens):
                t = tokens[i].lower()
                if t == 'name' and i+1 < len(tokens):
                    kv['name'] = tokens[i+1]
                    i += 2
                elif t == 'arrival' and i+1 < len(tokens):
                    kv['arrival'] = tokens[i+1]
                    i += 2
                elif t == 'burst' and i+1 < len(tokens):
                    kv['burst'] = tokens[i+1]
                    i += 2
                else:
                    i += 1
            if 'name' not in kv:
                error_and_exit("Error: Missing parameter name")
            if 'arrival' not in kv:
                error_and_exit("Error: Missing parameter arrival")
            if 'burst' not in kv:
                error_and_exit("Error: Missing parameter burst")
            p = Process(kv['name'], kv['arrival'], kv['burst'], proc_index)
            proc_index += 1
            processes.append(p)
        elif key == 'end':
            break
        else:
            # ignore unknown lines
            pass
        idx += 1

    for r in ['processcount', 'runfor', 'use']:
        if r not in params:
            error_and_exit(f"Error: Missing parameter {r}")

    if params['use'] not in ('fcfs', 'sjf', 'rr'):
        error_and_exit("Error: Invalid scheduling algorithm specified in use")

    if params['use'] == 'rr' and 'quantum' not in params:
        error_and_exit("Error: Missing quantum parameter when use is 'rr'")

    # set processcount to actual discovered processes if mismatch
    params['processes'] = processes
    return params

# formatting helper
def time_line(t, msg):
    return f"Time {t:3} : {msg}"

# ---------- FCFS (original behavior you had) ----------
def simulate_fcfs(processes, runfor, out_lines):
    # non-preemptive
    procs = sorted(processes, key=lambda p: (p.arrival, p.index))
    ready = []
    arrived = set()
    time = 0
    current = None

    while time < runfor:
        # arrivals at this tick
        for p in procs:
            if p.arrival == time and p.name not in arrived:
                arrived.add(p.name)
                out_lines.append(time_line(time, f"{p.name} arrived"))
                if p.remaining > 0:
                    ready.append(p)

        if current is None:
            if ready:
                current = ready.pop(0)
                if current.start_time is None:
                    current.start_time = time
                out_lines.append(time_line(time, f"{current.name} selected (burst {current.remaining:4})"))
            else:
                out_lines.append(time_line(time, "Idle"))
                time += 1
                continue

        # run current to completion or until runfor boundary
        while current and current.remaining > 0 and time < runfor:
            time += 1
            current.remaining -= 1
            # log arrivals that happen at this new tick
            for p in procs:
                if p.arrival == time and p.name not in arrived:
                    arrived.add(p.name)
                    out_lines.append(time_line(time, f"{p.name} arrived"))
                    if p.remaining > 0:
                        ready.append(p)
            if current.remaining == 0:
                current.finish_time = time
                out_lines.append(time_line(time, f"{current.name} finished"))
                current = None
                break

    out_lines.append(f"Finished at time {runfor:3}")

# ---------- Preemptive SJF (preempt only when new arrival has strictly smaller remaining) ----------
def simulate_sjf_preemptive(processes, runfor, out_lines):
    procs = sorted(processes, key=lambda p: (p.arrival, p.index))
    arrived = set()
    ready = []
    current = None
    time = 0

    while time < runfor:
        # collect new arrivals at time
        new_arrivals = []
        for p in procs:
            if p.arrival == time and p.name not in arrived:
                arrived.add(p.name)
                new_arrivals.append(p)
                out_lines.append(time_line(time, f"{p.name} arrived"))
                if p.remaining > 0:
                    ready.append(p)

        # determine candidates
        candidates = [p for p in ready if p.remaining > 0]
        if current and current.remaining > 0 and current not in candidates:
            candidates.append(current)

        if not candidates:
            out_lines.append(time_line(time, "Idle"))
            time += 1
            continue

        # decide whether to switch
        do_switch = False
        if current is None:
            do_switch = True
        else:
            # preempt only if some new arrival this tick has strictly smaller remaining
            preempting_new = any(na.remaining < current.remaining for na in new_arrivals)
            if preempting_new:
                do_switch = True
            else:
                do_switch = False

        if do_switch:
            # pick best (shortest remaining, tie by arrival/index)
            chosen = min(candidates, key=lambda p: (p.remaining, p.arrival, p.index))
            # if chosen was in ready list, remove it
            if chosen in ready:
                ready.remove(chosen)
            # if we are switching from a different current, put old current back into ready (if it exists and not finished)
            if current is not None and current is not chosen and current.remaining > 0:
                # only add previous current to ready if it wasn't already in ready
                if current not in ready:
                    ready.append(current)
            current = chosen
            if current.start_time is None:
                current.start_time = time
            out_lines.append(time_line(time, f"{current.name} selected (burst {current.remaining:4})"))

        # Execute one tick of current
        current.remaining -= 1
        time += 1

        # Note: arrivals at new time will be handled at top of next loop iteration
        if current.remaining == 0:
            current.finish_time = time
            out_lines.append(time_line(time, f"{current.name} finished"))
            current = None

    out_lines.append(f"Finished at time {runfor:3}")

# ---------- Round-Robin (fixed ordering: arrivals at boundary are enqueued BEFORE re-queueing the old process) ----------
def simulate_rr(processes, runfor, quantum, out_lines):
    procs = sorted(processes, key=lambda p: (p.arrival, p.index))
    arrived = set()
    ready = deque()
    current = None
    quantum_remaining = 0
    time = 0

    while time < runfor:
        # arrivals at this tick (time)
        for p in procs:
            if p.arrival == time and p.name not in arrived:
                arrived.add(p.name)
                out_lines.append(time_line(time, f"{p.name} arrived"))
                if p.remaining > 0:
                    ready.append(p)

        # If no current, pick next
        if current is None:
            if ready:
                current = ready.popleft()
                if current.start_time is None:
                    current.start_time = time
                quantum_remaining = quantum
                out_lines.append(time_line(time, f"{current.name} selected (burst {current.remaining:4})"))
            else:
                out_lines.append(time_line(time, "Idle"))
                time += 1
                continue

        # Execute one tick of current
        current.remaining -= 1
        quantum_remaining -= 1
        time += 1

        # arrivals at new time are logged and enqueued before we decide finish/quantum expiry
        for p in procs:
            if p.arrival == time and p.name not in arrived:
                arrived.add(p.name)
                out_lines.append(time_line(time, f"{p.name} arrived"))
                if p.remaining > 0:
                    ready.append(p)

        # check if finished
        if current.remaining == 0:
            current.finish_time = time
            out_lines.append(time_line(time, f"{current.name} finished"))
            current = None
            quantum_remaining = 0
        elif quantum_remaining == 0:
            # quantum expired; requeue current after arrivals (arrivals were appended above)
            ready.append(current)
            current = None

    out_lines.append(f"Finished at time {runfor:3}")

# ---------- Metrics and output formatting ----------
def append_metrics(processes, out_lines):
    # sort by process name or index — user examples use name order P01, P02...
    procs = sorted(processes, key=lambda p: p.name)
    for p in procs:
        if p.finish_time is None:
            out_lines.append(f"{p.name} did not finish")
        else:
            turnaround = p.finish_time - p.arrival
            wait = turnaround - p.burst
            response = p.start_time - p.arrival if p.start_time is not None else 0
            out_lines.append(f"{p.name} wait {wait:3d} turnaround {turnaround:3d} response {response:3d}")

def run_scheduler(params, out_lines):
    procs = params['processes']
    runfor = params['runfor']
    use = params['use']
    quantum = params.get('quantum', None)

    out_lines.append(f"{len(procs)} processes")
    if use == 'fcfs':
        out_lines.append("Using First-Come First-Served")
        simulate_fcfs(procs, runfor, out_lines)
    elif use == 'sjf':
        out_lines.append("Using preemptive Shortest Job First")
        simulate_sjf_preemptive(procs, runfor, out_lines)
    elif use == 'rr':
        out_lines.append("Using Round-Robin")
        out_lines.append(f"Quantum   {quantum}")
        out_lines.append("")  # blank line before timeline (matches sample spacing)
        simulate_rr(procs, runfor, quantum, out_lines)
    else:
        error_and_exit("Error: Unknown scheduling algorithm")

    out_lines.append("")  # blank line before metrics (match samples)
    append_metrics(procs, out_lines)

def main():
    if len(sys.argv) != 2:
        usage_and_exit()
    infile = sys.argv[1]
    params = parse_input_file(infile)

    out_lines = []
    run_scheduler(params, out_lines)

    # write to output file
    base = os.path.splitext(infile)[0]
    outfile = base + '.out'
    with open(outfile, 'w') as f:
        for line in out_lines:
            f.write(line + '\n')

    print(f"Wrote output to {outfile}")

if __name__ == '__main__':
    main()
