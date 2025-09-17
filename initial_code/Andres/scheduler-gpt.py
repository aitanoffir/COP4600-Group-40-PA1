#!/usr/bin/env python3
import sys
import os
from collections import deque

USAGE = "Usage: scheduler-gpt.py <input file>"

def parse_input(path):
    params = {
        "processcount": None,
        "runfor": None,
        "use": None,
        "quantum": None,
        "processes": []
    }
    if not os.path.exists(path):
        print(f"Error: File not found {path}")
        sys.exit(1)

    with open(path, "r") as f:
        lines = f.readlines()

    def strip_comment(line):
        if "#" in line:
            return line[:line.index("#")]
        return line

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        line = strip_comment(raw).strip()
        i += 1
        if not line:
            continue
        toks = line.split()
        if toks[0] == "processcount":
            if len(toks) < 2:
                print("Error: Missing parameter processcount")
                sys.exit(1)
            params["processcount"] = int(toks[1])
        elif toks[0] == "runfor":
            if len(toks) < 2:
                print("Error: Missing parameter runfor")
                sys.exit(1)
            params["runfor"] = int(toks[1])
        elif toks[0] == "use":
            if len(toks) < 2:
                print("Error: Missing parameter use")
                sys.exit(1)
            algo = toks[1].lower()
            if algo not in ("fcfs", "sjf", "rr"):
                print("Error: Invalid algorithm in 'use' parameter")
                sys.exit(1)
            params["use"] = algo
        elif toks[0] == "quantum":
            if len(toks) < 2:
                print("Error: Missing parameter quantum")
                sys.exit(1)
            params["quantum"] = int(toks[1])
        elif toks[0] == "process":
            # expected: process name A arrival 0 burst 5
            toks = line.split()
            try:
                name = toks[toks.index("name")+1]
                arrival = int(toks[toks.index("arrival")+1])
                burst = int(toks[toks.index("burst")+1])
            except Exception:
                print("Error: Malformed process line")
                sys.exit(1)
            params["processes"].append({
                "name": name,
                "arrival": arrival,
                "burst": burst,
                "remaining": burst,
                "start_time": None,
                "finish_time": None
            })
        elif toks[0] == "end":
            break
        else:
            # Ignore unknown lines that are just whitespace
            continue

    # Validate required params
    required = ["processcount", "runfor", "use"]
    for p in required:
        if params[p] is None:
            print(f"Error: Missing parameter {p}")
            sys.exit(1)

    if params["use"] == "rr" and params["quantum"] is None:
        print("Error: Missing quantum parameter when use is 'rr'")
        sys.exit(1)

    if params["processcount"] is None or len(params["processes"]) != params["processcount"]:
        # If count doesn't match, treat as error per common course spec
        print("Error: processcount does not match number of processes")
        sys.exit(1)

    # Sort processes by arrival then name for deterministic tie-breaking
    params["processes"].sort(key=lambda p: (p["arrival"], p["name"]))
    return params

def algo_name(use):
    if use == "fcfs":
        return "First-Come First-Served"
    if use == "sjf":
        return "preemptive Shortest Job First"
    if use == "rr":
        return "Round-Robin"
    return use

def print_header(out, nproc, use, quantum):
    out.append(f"  {nproc} processes")
    out.append(f"Using {algo_name(use)}")
    if use == "rr":
        out.append(f"Quantum   {quantum}\n")

def compute_metrics(proc):
    if proc["finish_time"] is None:
        return None
    turnaround = proc["finish_time"] - proc["arrival"]
    wait = turnaround - proc["burst"]
    response = (proc["start_time"] - proc["arrival"]) if proc["start_time"] is not None else 0
    return wait, turnaround, response


def simulate(params):
    procs = [dict(p) for p in params["processes"]]
    runfor = params["runfor"]
    use = params["use"]
    quantum = params["quantum"]
    out = []
    print_header(out, len(procs), use, quantum)

    time = 0
    ready = deque()
    current = None
    rr_qleft = None
    arrived_idx = 0
    rr_carry = []  # preempted-at-previous-tick processes to enqueue next tick after arrivals

    def select_proc(p, now):
        nonlocal current, rr_qleft
        current = p
        if p["start_time"] is None:
            p["start_time"] = now
        out.append(f"Time {now:3d} : {p['name']} selected (burst {p['remaining']:3d})")
        if use == "rr":
            rr_qleft = quantum

    while time < runfor:
        # (1) Arrivals at this time
        while arrived_idx < len(procs) and procs[arrived_idx]["arrival"] == time:
            p = procs[arrived_idx]
            out.append(f"Time {time:3d} : {p['name']} arrived")
            if use in ("fcfs", "rr"):
                ready.append(p)
            arrived_idx += 1

        # (1b) RR: enqueue carried preempted proc AFTER arrivals
        if use == "rr" and rr_carry:
            for p in rr_carry:
                ready.append(p)
            rr_carry.clear()

        # (2) If idle, pick next
        if current is None:
            if use in ("fcfs", "rr"):
                if ready:
                    select_proc(ready.popleft(), time)
            elif use == "sjf":
                cands = [p for p in procs if p["arrival"] <= time and p["remaining"] > 0]
                if cands:
                    best = min(cands, key=lambda p: (p["remaining"], p["name"]))
                    select_proc(best, time)

        # (3) Execute one tick or idle
        if current is None:
            out.append(f"Time {time:3d} : Idle")
        else:
            current["remaining"] -= 1
            if use == "rr":
                rr_qleft -= 1

            # (4) End-of-tick outcomes
            if current["remaining"] == 0:
                current["finish_time"] = time + 1
                out.append(f"Time {time+1:3d} : {current['name']} finished")
                current = None
                rr_qleft = None
            else:
                if use == "sjf":
                    pass  # preemption considered at step (5)
                elif use == "rr":
                    if rr_qleft == 0:
                        # Time slice expired; carry to next tick (after arrivals)
                        rr_carry.append(current)
                        current = None
                        rr_qleft = None

        # (5) SJF preemption: if a shorter job will be available at next tick
        if use == "sjf" and current is not None:
            cands = [p for p in procs if p["arrival"] <= time+1 and p["remaining"] > 0]
            if cands:
                best = min(cands, key=lambda p: (p["remaining"], p["name"]))
                if best is not current and best["remaining"] < current["remaining"]:
                    current = None  # will reselect next loop

        time += 1

    out.append(f"Finished at time {runfor:3d}\n")

    for p in sorted(procs, key=lambda x: x["name"]):
        if p["finish_time"] is None:
            out.append(f"{p['name']} did not finish")
        else:
            metrics = compute_metrics(p)
            wait, turnaround, response = metrics
            out.append(f"{p['name']} wait {wait:3d} turnaround {turnaround:3d} response   {response}")

    return out

def main():
    if len(sys.argv) != 2:
        print(USAGE)
        sys.exit(1)
    infile = sys.argv[1]
    if not infile.endswith(".in"):
        print("Error: Input filename must have .in extension")
        sys.exit(1)

    params = parse_input(infile)
    out_lines = simulate(params)

    base = os.path.splitext(infile)[0]
    outfile = base + ".out"
    with open(outfile, "w") as f:
        f.write("\n".join(out_lines) + "\n")

if __name__ == "__main__":
    main()
