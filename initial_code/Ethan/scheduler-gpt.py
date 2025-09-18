import sys
from collections import deque
import os

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time = None
        self.finish_time = None

def parse_input(filename):
    processes = []
    algorithm = None
    quantum = None
    runtime = None
    with open(filename, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens:
                continue
            if tokens[0] == "use":
                if tokens[1].lower() == "fcfs":
                    algorithm = "fifo"
                elif tokens[1].lower() == "sjf":
                    algorithm = "sjf"
                elif tokens[1].lower() == "rr":
                    algorithm = "rr"
            elif tokens[0] == "runfor":
                runtime = int(tokens[1])
            elif tokens[0] == "process":
                name = tokens[2]
                arrival = int(tokens[4])
                burst = int(tokens[6])
                processes.append(Process(name, arrival, burst))
            elif tokens[0] == "quantum":
                quantum = int(tokens[1])
            elif tokens[0] == "end":
                break
    return processes, algorithm, runtime, quantum

# ---------------- FCFS ----------------
def fifo(processes, runtime):
    time = 0
    log = []
    ready_queue = deque()
    running = None

    while time < runtime:
        # 1. Arrivals
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3d} : {p.name} arrived")
                ready_queue.append(p)

        # 2. Finishes
        if running and running.remaining == 0:
            running.finish_time = time
            log.append(f"Time {time:3d} : {running.name} finished")
            running = None

        # 3. Selection
        if running is None and ready_queue:
            running = ready_queue.popleft()
            if running.start_time is None:
                running.start_time = time
            log.append(f"Time {time:3d} : {running.name} selected (burst {running.remaining:3d})")

        # 4. Execute
        if running:
            running.remaining -= 1
        else:
            log.append(f"Time {time:3d} : Idle")

        time += 1

    log.append(f"Finished at time {runtime:3d}")
    return log

# ---------------- SJF (preemptive) ----------------
def sjf_preemptive(processes, runtime):
    time = 0
    log = []
    ready = []
    running = None

    while time < runtime:
        # 1. Arrivals
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3d} : {p.name} arrived")
                ready.append(p)

        # 2. Finishes
        if running and running.remaining == 0:
            running.finish_time = time
            log.append(f"Time {time:3d} : {running.name} finished")
            running = None

        # 3. Selection (shortest job first)
        if running:
            ready.append(running)
        if ready:
            ready.sort(key=lambda p: (p.remaining, p.arrival))
            next_proc = ready.pop(0)
            if next_proc != running:
                running = next_proc
                if running.start_time is None:
                    running.start_time = time
                log.append(f"Time {time:3d} : {running.name} selected (burst {running.remaining:3d})")
            else:
                running = next_proc
        else:
            running = None

        # 4. Execute
        if running:
            running.remaining -= 1
        else:
            log.append(f"Time {time:3d} : Idle")

        time += 1

    log.append(f"Finished at time {runtime:3d}")
    return log

# ---------------- Round Robin ----------------
def round_robin(processes, runtime, quantum):
    time = 0
    log = []
    ready_queue = deque()
    running = None
    quantum_counter = 0

    while time < runtime:
        # 1. Arrivals (enqueue first)
        for p in processes:
            if p.arrival == time:
                log.append(f"Time {time:3d} : {p.name} arrived")
                ready_queue.append(p)

        # 2. Finishes
        if running and running.remaining == 0:
            running.finish_time = time
            log.append(f"Time {time:3d} : {running.name} finished")
            running = None
            quantum_counter = 0

        # 3. Quantum expiration (enqueue AFTER arrivals of this tick)
        elif running and quantum_counter == quantum:
            ready_queue.append(running)
            running = None
            quantum_counter = 0

        # 4. Selection
        if running is None and ready_queue:
            running = ready_queue.popleft()
            if running.start_time is None:
                running.start_time = time
            log.append(f"Time {time:3d} : {running.name} selected (burst {running.remaining:3d})")
            quantum_counter = 0

        # 5. Execute
        if running:
            running.remaining -= 1
            quantum_counter += 1
        else:
            log.append(f"Time {time:3d} : Idle")

        time += 1

    log.append(f"Finished at time {runtime:3d}")
    return log

# ---------------- Metrics ----------------
def calculate_metrics(processes):
    metrics = []
    for p in sorted(processes, key=lambda x: x.name):
        if p.finish_time:
            turnaround = p.finish_time - p.arrival
            wait = turnaround - p.burst
            response = p.start_time - p.arrival
            metrics.append(f"{p.name} wait {wait:3d} turnaround {turnaround:3d} response {response:3d}")
        else:
            metrics.append(f"{p.name} did not finish")
    return metrics

# ---------------- Main ----------------
if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".in"):
        print("Usage: python scheduler-gpt.py inputFile.in")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + ".out"

    processes, algorithm, runtime, quantum = parse_input(input_file)

    output_lines = []
    # process count spacing: <10 → two spaces, >=10 → one space
    if len(processes) < 10:
        output_lines.append(f"  {len(processes)} processes")
    else:
        output_lines.append(f" {len(processes)} processes")

    if algorithm == "fifo":
        output_lines.append("Using First-Come First-Served")
        log = fifo(processes, runtime)
    elif algorithm == "sjf":
        output_lines.append("Using preemptive Shortest Job First")
        log = sjf_preemptive(processes, runtime)
    elif algorithm == "rr":
        output_lines.append("Using Round-Robin")
        output_lines.append(f"Quantum {quantum:3d}")
        output_lines.append("")  # blank line after quantum
        log = round_robin(processes, runtime, quantum)
    else:
        sys.exit("Unknown algorithm")

    output_lines.extend(log)
    output_lines.append("")
    output_lines.extend(calculate_metrics(processes))

    with open(output_file, "w") as f:
        f.write("\n".join(output_lines) + "\n")
