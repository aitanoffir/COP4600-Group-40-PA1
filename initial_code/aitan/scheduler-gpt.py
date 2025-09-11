#!/usr/bin/env python3
import sys
import os

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time = -1
        self.finish_time = -1
        self.wait_time = 0
        self.response_time = -1
        self.turnaround_time = 0
        
def parse_input(filename):
    """Parse the input file and return scheduling parameters and processes."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found")
        sys.exit(1)
    
    processes = []
    process_count = None
    run_for = None
    algorithm = None
    quantum = None
    
    for line in lines:
        # Remove comments and strip whitespace
        if '#' in line:
            line = line[:line.index('#')]
        line = line.strip()
        
        if not line:
            continue
            
        parts = line.split()
        
        if parts[0] == 'processcount':
            if len(parts) < 2:
                print("Error: Missing parameter processcount.")
                sys.exit(1)
            process_count = int(parts[1])
            
        elif parts[0] == 'runfor':
            if len(parts) < 2:
                print("Error: Missing parameter runfor.")
                sys.exit(1)
            run_for = int(parts[1])
            
        elif parts[0] == 'use':
            if len(parts) < 2:
                print("Error: Missing parameter use.")
                sys.exit(1)
            algorithm = parts[1]
            
        elif parts[0] == 'quantum':
            if len(parts) < 2:
                print("Error: Missing parameter quantum.")
                sys.exit(1)
            quantum = int(parts[1])
            
        elif parts[0] == 'process':
            # Parse process line: process name NAME arrival TIME burst TIME
            name = None
            arrival = None
            burst = None
            
            i = 1
            while i < len(parts):
                if parts[i] == 'name' and i + 1 < len(parts):
                    name = parts[i + 1]
                    i += 2
                elif parts[i] == 'arrival' and i + 1 < len(parts):
                    arrival = int(parts[i + 1])
                    i += 2
                elif parts[i] == 'burst' and i + 1 < len(parts):
                    burst = int(parts[i + 1])
                    i += 2
                else:
                    i += 1
            
            if name is None or arrival is None or burst is None:
                print("Error: Missing parameter in process definition.")
                sys.exit(1)
                
            processes.append(Process(name, arrival, burst))
            
        elif parts[0] == 'end':
            break
    
    # Validate required parameters
    if process_count is None:
        print("Error: Missing parameter processcount.")
        sys.exit(1)
    if run_for is None:
        print("Error: Missing parameter runfor.")
        sys.exit(1)
    if algorithm is None:
        print("Error: Missing parameter use.")
        sys.exit(1)
    if algorithm == 'rr' and quantum is None:
        print("Error: Missing quantum parameter when use is 'rr'")
        sys.exit(1)
    
    return process_count, run_for, algorithm, quantum, processes

def fcfs_scheduler(processes, run_for):
    """First-Come First-Served scheduler."""
    output = []
    time = 0
    ready_queue = []
    current_process = None
    finished_processes = []
    
    # Sort processes by arrival time, then by name
    processes_copy = sorted(processes, key=lambda p: (p.arrival, p.name))
    
    while time < run_for:
        # Collect all events that happen at this time
        arrivals = []
        finish_event = None
        
        # Check for arriving processes
        for p in processes_copy:
            if p.arrival == time:
                arrivals.append(p)
        
        # Check if current process finishes at this time
        if current_process and current_process.remaining == 0:
            finish_event = current_process
        
        # Output events in correct order: arrivals first, then finishes
        for p in arrivals:
            output.append(f"Time{time:4} : {p.name} arrived")
            ready_queue.append(p)
        
        if finish_event:
            output.append(f"Time{time:4} : {finish_event.name} finished")
            finished_processes.append(finish_event)
            current_process = None
        
        # Select next process if needed
        if current_process is None and ready_queue:
            current_process = ready_queue.pop(0)
            current_process.start_time = time
            current_process.response_time = time - current_process.arrival
            output.append(f"Time{time:4} : {current_process.name} selected (burst{current_process.burst:4})")
        
        # Execute current process or idle
        if current_process and current_process.remaining > 0:
            current_process.remaining -= 1
            if current_process.remaining == 0:
                # Process will finish at next time tick
                current_process.finish_time = time + 1
                current_process.turnaround_time = current_process.finish_time - current_process.arrival
                current_process.wait_time = current_process.turnaround_time - current_process.burst
        elif current_process is None:
            output.append(f"Time{time:4} : Idle")
        
        time += 1
    
    return output, finished_processes

def sjf_scheduler(processes, run_for):
    """Pre-emptive Shortest Job First scheduler."""
    output = []
    time = 0
    ready_queue = []
    current_process = None
    finished_processes = []
    
    # Create copies of processes to track
    processes_copy = [Process(p.name, p.arrival, p.burst) for p in processes]
    
    while time < run_for:
        # Collect all events that happen at this time
        arrivals = []
        finish_event = None
        
        # Check for arriving processes
        for p in processes_copy:
            if p.arrival == time and p.finish_time == -1:  # Not yet finished
                arrivals.append(p)
        
        # Check if current process finishes at this time
        if current_process and current_process.remaining == 0:
            finish_event = current_process
        
        # Output arrivals first
        for p in arrivals:
            output.append(f"Time{time:4} : {p.name} arrived")
            ready_queue.append(p)
        
        # Output finish event
        if finish_event:
            output.append(f"Time{time:4} : {finish_event.name} finished")
            finished_processes.append(finish_event)
            current_process = None
        
        # Check for preemption after arrivals
        if current_process and arrivals:
            # Check if any new arrival has shorter remaining time
            for p in arrivals:
                if p.remaining < current_process.remaining:
                    ready_queue.append(current_process)
                    current_process = None
                    break
        
        # Select shortest job if no current process
        if current_process is None and ready_queue:
            # Sort by remaining time, then by name for tie-breaking
            ready_queue.sort(key=lambda p: (p.remaining, p.name))
            current_process = ready_queue.pop(0)
            
            # Set start time and response time if first time selected
            if current_process.start_time == -1:
                current_process.start_time = time
                current_process.response_time = time - current_process.arrival
            
            output.append(f"Time{time:4} : {current_process.name} selected (burst{current_process.remaining:4})")
        
        # Execute current process or idle
        if current_process and current_process.remaining > 0:
            current_process.remaining -= 1
            if current_process.remaining == 0:
                # Process will finish at next time tick
                current_process.finish_time = time + 1
                current_process.turnaround_time = current_process.finish_time - current_process.arrival
                current_process.wait_time = current_process.turnaround_time - current_process.burst
        elif current_process is None:
            output.append(f"Time{time:4} : Idle")
        
        time += 1
    
    return output, finished_processes

def rr_scheduler(processes, run_for, quantum):
    """Round Robin scheduler."""
    output = []
    time = 0
    ready_queue = []
    current_process = None
    quantum_remaining = 0
    finished_processes = []
    
    # Create copies of processes to track
    processes_copy = [Process(p.name, p.arrival, p.burst) for p in processes]
    
    while time < run_for:
        # Collect all events that happen at this time
        arrivals = []
        finish_event = None
        
        # Check for arriving processes
        for p in processes_copy:
            if p.arrival == time and p.finish_time == -1:  # Not yet finished
                arrivals.append(p)
        
        # Check if current process finishes at this time
        if current_process and current_process.remaining == 0:
            finish_event = current_process
        
        # Output arrivals first
        for p in arrivals:
            output.append(f"Time{time:4} : {p.name} arrived")
            ready_queue.append(p)
        
        # Output finish event and handle completion
        if finish_event:
            output.append(f"Time{time:4} : {finish_event.name} finished")
            finished_processes.append(finish_event)
            current_process = None
            quantum_remaining = 0
        
        # Check if quantum expired for current process
        if current_process and quantum_remaining == 0 and current_process.remaining > 0:
            ready_queue.append(current_process)
            current_process = None
        
        # Select next process if no current process
        if current_process is None and ready_queue:
            current_process = ready_queue.pop(0)
            quantum_remaining = quantum
            
            # Set start time and response time if first time selected
            if current_process.start_time == -1:
                current_process.start_time = time
                current_process.response_time = time - current_process.arrival
            
            output.append(f"Time{time:4} : {current_process.name} selected (burst{current_process.remaining:4})")
        
        # Execute current process or idle
        if current_process and current_process.remaining > 0:
            current_process.remaining -= 1
            quantum_remaining -= 1
            if current_process.remaining == 0:
                # Process will finish at next time tick
                current_process.finish_time = time + 1
                current_process.turnaround_time = current_process.finish_time - current_process.arrival
                current_process.wait_time = current_process.turnaround_time - current_process.burst
        elif current_process is None:
            output.append(f"Time{time:4} : Idle")
        
        time += 1
    
    return output, finished_processes

def write_output(filename, process_count, algorithm, quantum, output, finished_processes, run_for, all_processes):
    """Write the output to file."""
    with open(filename, 'w') as f:
        # Header
        f.write(f"{process_count:3} processes\n")
        
        # Algorithm name
        if algorithm == 'fcfs':
            f.write("Using First-Come First-Served\n")
        elif algorithm == 'sjf':
            f.write("Using preemptive Shortest Job First\n")
        elif algorithm == 'rr':
            f.write("Using Round-Robin\n")
            f.write(f"Quantum {quantum:3}\n")
            f.write("\n")  # Add blank line after Quantum for RR
        
        # Timeline events
        for line in output:
            f.write(line + "\n")
        
        # Finish time
        f.write(f"Finished at time{run_for:4}\n\n")
        
        # Process statistics
        # Sort by name for consistent output
        finished_processes.sort(key=lambda p: p.name)
        for p in finished_processes:
            f.write(f"{p.name} wait{p.wait_time:4} turnaround{p.turnaround_time:4} response{p.response_time:4}\n")
        
        # Check for unfinished processes
        finished_names = {p.name for p in finished_processes}
        for p in all_processes:
            if p.name not in finished_names:
                f.write(f"{p.name} did not finish\n")

def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: scheduler-get.py <input file>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    
    # Check if input file has .in extension
    if not input_filename.endswith('.in'):
        print("Error: Input file must have .in extension")
        sys.exit(1)
    
    # Generate output filename in current directory
    # Extract just the base filename from the path
    base_filename = os.path.basename(input_filename)
    output_filename = base_filename[:-3] + '.out'
    
    # Parse input
    process_count, run_for, algorithm, quantum, processes = parse_input(input_filename)
    
    # Run appropriate scheduler
    if algorithm == 'fcfs':
        output, finished = fcfs_scheduler(processes, run_for)
    elif algorithm == 'sjf':
        output, finished = sjf_scheduler(processes, run_for)
    elif algorithm == 'rr':
        output, finished = rr_scheduler(processes, run_for, quantum)
    else:
        print(f"Error: Unknown algorithm '{algorithm}'")
        sys.exit(1)
    
    # Write output
    write_output(output_filename, process_count, algorithm, quantum, output, finished, run_for, processes)
    
    print(f"Output written to {output_filename}")

if __name__ == "__main__":
    main()