#!/usr/bin/env python3
import sys
import os

# ------------------------------
# Process structure
# ------------------------------
class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time = None
        self.finish_time = None
        self.response_time = None

# ------------------------------
# Utility metrics
# ------------------------------
def calculate_metrics(processes):
    results = []
    for p in processes:
        if p.finish_time is None:
            results.append(f"{p.name} did not finish")
            continue
        turnaround = p.finish_time - p.arrival
        wait = turnaround - p.burst
        response = p.response_time - p.arrival if p.response_time is not None else 0
        results.append(f"{p.name} wait   {wait} turnaround  {turnaround} response   {response}")
    return results

# ------------------------------
# FIFO (First Come First Serve)
# ------------------------------
def fifo(processes, runtime, log):
    time = 0
    processes.sort(key=lambda p: p.arrival)
    ready = []
    finished = []

    while time < runtime:
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3} : {p.name} arrived")
                ready.append(p)

        if ready:
            current = ready.pop(0)
            if current.response_time is None:
                current.response_time = time
            log.append(f"Time {time:3} : {current.name} selected (burst   {current.remaining})")

            for _ in range(current.remaining):
                time += 1
                for p in processes:
                    if p.arrival == time:
                        log.append(f"Time {time:3} : {p.name} arrived")
                if time >= runtime:
                    break
            current.finish_time = time
            log.append(f"Time {time:3} : {current.name} finished")
            finished.append(current)
        else:
            log.append(f"Time {time:3} : Idle")
            time += 1

    log.append(f"Finished at time  {runtime}")
    return processes

# ------------------------------
# Preemptive Shortest Job First
# ------------------------------
def sjf(processes, runtime, log):
    time = 0
    ready = []
    processes.sort(key=lambda p: p.arrival)

    while time < runtime:
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3} : {p.name} arrived")
                ready.append(p)

        ready = [p for p in ready if p.remaining > 0]
        if ready:
            current = min(ready, key=lambda p: p.remaining)
            if current.response_time is None:
                current.response_time = time
                log.append(f"Time {time:3} : {current.name} selected (burst   {current.remaining})")
            elif log[-1].find(f"{current.name} selected") == -1:
                log.append(f"Time {time:3} : {current.name} selected (burst   {current.remaining})")

            current.remaining -= 1
            time += 1
            if current.remaining == 0:
                current.finish_time = time
                log.append(f"Time {time:3} : {current.name} finished")
        else:
            log.append(f"Time {time:3} : Idle")
            time += 1

    log.append(f"Finished at time  {runtime}")
    return processes

# ------------------------------
# Round Robin
# ------------------------------
def rr(processes, runtime, quantum, log):
    time = 0
    ready = []
    processes.sort(key=lambda p: p.arrival)
    queue = []

    while time < runtime:
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3} : {p.name} arrived")
                queue.append(p)

        if queue:
            current = queue.pop(0)
            if current.response_time is None:
                current.response_time = time
            log.append(f"Time {time:3} : {current.name} selected (burst   {current.remaining})")

            run_time = min(quantum, current.remaining)
            for _ in range(run_time):
                time += 1
                for p in processes:
                    if p.arrival == time:
                        log.append(f"Time {time:3} : {p.name} arrived")
                        queue.append(p)
                current.remaining -= 1
                if current.remaining == 0:
                    current.finish_time = time
                    log.append(f"Time {time:3} : {current.name} finished")
                    break
                if time >= runtime:
                    break
            if current.remaining > 0:
                queue.append(current)
        else:
            log.append(f"Time {time:3} : Idle")
            time += 1

    log.append(f"Finished at time  {runtime}")
    return processes

# ------------------------------
# Input Parser
# ------------------------------
def parse_input(filename):
    processes = []
    algo = None
    runtime = None
    quantum = None

    with open(filename, "r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts or parts[0].startswith("#"):
                continue
            if parts[0] == "processcount":
                count = int(parts[1])
            elif parts[0] == "runfor":
                runtime = int(parts[1])
            elif parts[0] == "use":
                algo = parts[1]
            elif parts[0] == "quantum":
                quantum = int(parts[1])
            elif parts[0] == "process":
                name = parts[2]
                arrival = int(parts[4])
                burst = int(parts[6])
                processes.append(Process(name, arrival, burst))
            elif parts[0] == "end":
                break

    if algo == "rr" and quantum is None:
        print("Error: Missing quantum parameter when use is 'rr'")
        sys.exit(1)
    if runtime is None or algo is None:
        print("Error: Missing parameter runfor or use")
        sys.exit(1)

    return processes, algo, runtime, quantum

# ------------------------------
# Main
# ------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: scheduler-gpt.py <input file>")
        sys.exit(1)

    infile = sys.argv[1]
    if not infile.endswith(".in"):
        print("Error: Input file must have .in extension")
        sys.exit(1)

    outfile = os.path.splitext(infile)[0] + ".out"

    processes, algo, runtime, quantum = parse_input(infile)
    log = []

    # Header
    log.append(f"{len(processes)} processes")
    if algo == "fcfs":
        log.append("Using First Come First Serve")
        processes = fifo(processes, runtime, log)
    elif algo == "sjf":
        log.append("Using preemptive Shortest Job First")
        processes = sjf(processes, runtime, log)
    elif algo == "rr":
        log.append("Using Round-Robin")
        log.append(f"Quantum   {quantum}")
        processes = rr(processes, runtime, quantum, log)

    # Summary
    metrics = calculate_metrics(processes)
    log.extend(metrics)

    with open(outfile, "w") as f:
        for line in log:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
