import sys
import collections
import os

class Process:
    def __init__(self, name, arrival_time, burst_time):
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_burst_time = burst_time
        self.start_time = -1
        self.finish_time = -1
        self.wait_time = 0
        self.turnaround_time = 0
        self.response_time = -1
        self.last_run_time = -1
        self.total_wait_time = 0

def parse_input_file(file_path):
    """
    Parses the input file to extract simulation parameters and process details.
    """
    processes = []
    runfor = 0
    scheduler_type = ""
    quantum = 0
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                
                parts = line.split()
                directive = parts[0]
                
                if directive == "processcount":
                    pass
                elif directive == "runfor":
                    runfor = int(parts[1])
                elif directive == "use":
                    scheduler_type = parts[1]
                elif directive == "quantum":
                    quantum = int(parts[1])
                elif directive == "process":
                    name = parts[2]
                    arrival = int(parts[4])
                    burst = int(parts[6])
                    processes.append(Process(name, arrival, burst))
                elif directive == "end":
                    break
                    
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
        
    return processes, runfor, scheduler_type, quantum

def calculate_metrics(processes):
    """
    Calculates and prints the final performance metrics for each process.
    """
    metrics_output = ""
    for p in processes:
        p.turnaround_time = p.finish_time - p.arrival_time
        p.wait_time = p.turnaround_time - p.burst_time
        metrics_output += f"{p.name} wait {p.wait_time:3} turnaround {p.turnaround_time:3} response {p.response_time:3}\n"
    return metrics_output

def write_output_file(input_file, output_directory, processes, scheduler_type, runfor, timeline_output, quantum):
    """
    Writes the simulation output to a file in the specified directory.
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    base_name = os.path.basename(input_file)
    output_file_name = os.path.splitext(base_name)[0] + ".out"
    output_path = os.path.join(output_directory, output_file_name)

    with open(output_path, 'w') as f:
        if len(processes) > 9:
            f.write(f" {len(processes)} processes\n")
        else:
            f.write(f"  {len(processes)} processes\n")
        
        if scheduler_type == "fcfs":
            f.write("Using First-Come First-Served")
        elif scheduler_type == "sjf":
            f.write("Using preemptive Shortest Job First")
        elif scheduler_type == "rr":
            f.write("Using Round-Robin\n")
            f.write(f"Quantum   {quantum}\n")
        
        f.write("\n")
        f.write(timeline_output)
        
        f.write(f"Finished at time  {runfor}\n\n")

        f.write(calculate_metrics(processes))

def run_simulation(processes, runfor, scheduler_type, quantum):
    """
    Runs the scheduling simulation based on the chosen algorithm.
    """
    timeline = []
    ready_queue = collections.deque()
    arrived_processes = collections.deque(sorted(processes, key=lambda p: p.arrival_time))
    finished_processes = []
    current_process = None
    
    for time in range(runfor + 1):
        # 1. Handle new process arrivals at the current time unit
        while arrived_processes and arrived_processes[0].arrival_time <= time:
            process = arrived_processes.popleft()
            timeline.append(f"Time {time:3} : {process.name} arrived\n")
            ready_queue.append(process)

        # 2. Check for preemption or completion from the previous time step
        if current_process:
            if current_process.remaining_burst_time <= 0:
                current_process.finish_time = time
                finished_processes.append(current_process)
                timeline.append(f"Time {time:3} : {current_process.name} finished\n")
                current_process = None
            elif scheduler_type == "sjf" and ready_queue:
                shortest_job = min(ready_queue, key=lambda p: (p.remaining_burst_time, p.arrival_time))
                if shortest_job.remaining_burst_time < current_process.remaining_burst_time:
                    # Preempt the current process
                    ready_queue.append(current_process)
                    current_process = None
            elif scheduler_type == "rr" and quantum > 0 and (time - current_process.last_run_time) >= quantum:
                # Preempt the current process due to quantum expiration
#                timeline.append(f"Time {time:3} : {current_process.name} preempted\n")
                ready_queue.append(current_process)
                current_process = None

        # 3. Select a new process if the CPU is idle
        if not current_process and ready_queue:
            if scheduler_type == "sjf":
                # Sort the ready queue to find the shortest job
                ready_queue = collections.deque(sorted(list(ready_queue), key=lambda p: (p.remaining_burst_time, p.arrival_time)))
            
            current_process = ready_queue.popleft()
            
            if current_process.response_time == -1:
                current_process.response_time = time - current_process.arrival_time

            current_process.last_run_time = time
            timeline.append(f"Time {time:3} : {current_process.name} selected (burst {current_process.remaining_burst_time:3})\n")
        
        # 4. Run the current process for one time unit, but only if within the simulation time
        if time < runfor:
            if current_process:
                current_process.remaining_burst_time -= 1
            elif not current_process and not ready_queue:
                timeline.append(f"Time {time:3} : Idle\n")
    
    return "".join(timeline)

def main():
    print("Scheduler script started...")
    if len(sys.argv) < 2:
        print("Usage: python scheduler.py <input-file>")
        return
        
    input_file = sys.argv[1]
    
    processes, runfor, scheduler_type, quantum = parse_input_file(input_file)

    if scheduler_type == "rr" and quantum == 0:
        print("Error: Quantum value not specified for Round Robin scheduler.")
        return

    processes.sort(key=lambda p: p.arrival_time)
    
    timeline_output = run_simulation(processes, runfor, scheduler_type, quantum)

    processes.sort(key=lambda p: p.name)
    
    output_directory = "Output_Files"
    
    write_output_file(input_file, output_directory, processes, scheduler_type, runfor, timeline_output, quantum)
    print(f"Output written to {os.path.join(output_directory, os.path.basename(input_file).replace('.in', '.out'))}")

if __name__ == "__main__":
    main()
