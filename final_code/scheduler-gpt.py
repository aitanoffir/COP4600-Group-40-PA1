#Group-40 Members: Aitan Offir, Andres Arzola, Anthony Mahon, Ethan Niessner, Joshua Larenas


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

def calculate_statistics(output, finished_processes, run_for, all_processes):
    """Calculate scheduling statistics for HTML report."""
    stats = {}

    # Calculate averages for finished processes
    if finished_processes:
        avg_wait = sum(p.wait_time for p in finished_processes) / len(finished_processes)
        avg_turnaround = sum(p.turnaround_time for p in finished_processes) / len(finished_processes)
        avg_response = sum(p.response_time for p in finished_processes) / len(finished_processes)
    else:
        avg_wait = avg_turnaround = avg_response = 0


    stats['avg_wait_time'] = round(avg_wait, 2)
    stats['avg_turnaround_time'] = round(avg_turnaround, 2)
    stats['avg_response_time'] = round(avg_response, 2)

    return stats

def parse_timeline_events(output):
    """Parse timeline output to extract events for HTML visualization."""
    events = []
    for line in output:
        if line.startswith('Time'):
            parts = line.split(':', 1)
            time = int(parts[0].replace('Time', '').strip())
            event = parts[1].strip()

            # Categorize events
            if 'arrived' in event:
                event_type = 'arrival'
                process_name = event.split()[0]
            elif 'selected' in event:
                event_type = 'selection'
                process_name = event.split()[0]
            elif 'finished' in event:
                event_type = 'completion'
                process_name = event.split()[0]
            elif 'Idle' in event:
                event_type = 'idle'
                process_name = 'CPU'
            else:
                event_type = 'other'
                process_name = ''

            events.append({
                'time': time,
                'type': event_type,
                'process': process_name,
                'description': event
            })

    return events

def create_gantt_data(output, run_for):
    """Create Gantt chart data structure from timeline output."""
    gantt_data = {}
    current_process = None
    current_start = None
    execution_periods = []

    for i in range(run_for):
        # Find what happened at this time
        executing_process = None
        for line in output:
            if line.startswith(f'Time{i:4}'):
                if 'selected' in line:
                    executing_process = line.split()[2]
                elif 'Idle' in line:
                    executing_process = 'IDLE'
                break

        # If no explicit event, continue with current process
        if executing_process is None:
            executing_process = current_process

        # Handle process changes
        if executing_process != current_process:
            # End previous period
            if current_process is not None and current_start is not None:
                execution_periods.append({
                    'process': current_process,
                    'start': current_start,
                    'end': i,
                    'duration': i - current_start
                })

            # Start new period
            current_process = executing_process
            current_start = i

    # End final period
    if current_process is not None and current_start is not None:
        execution_periods.append({
            'process': current_process,
            'start': current_start,
            'end': run_for,
            'duration': run_for - current_start
        })

    # Group by process for Gantt chart
    for period in execution_periods:
        process = period['process']
        if process not in gantt_data:
            gantt_data[process] = []
        gantt_data[process].append(period)

    return gantt_data

def generate_html_report(filename, process_count, algorithm, quantum, output, finished_processes, run_for, all_processes):
    """Generate an HTML report with interactive visualizations."""
    # Calculate statistics
    stats = calculate_statistics(output, finished_processes, run_for, all_processes)
    events = parse_timeline_events(output)

    # Algorithm name for display
    algorithm_names = {
        'fcfs': 'First-Come First-Served (FCFS)',
        'sjf': 'Shortest Job First (SJF) - Preemptive',
        'rr': 'Round Robin (RR)'
    }
    algorithm_display = algorithm_names.get(algorithm, algorithm.upper())

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Process Scheduler Report - {algorithm_display}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 30px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(145deg, #ffffff, #f0f0f0);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }}

        .stat-icon {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .stat-value {{
            font-size: 2.2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #666;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            margin-bottom: 40px;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}


        .process-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        }}

        .process-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        .process-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }}

        .process-table tr:hover td {{
            background-color: #f8f9ff;
        }}

        .process-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        .timeline {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: #fafafa;
        }}

        .timeline-event {{
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: background-color 0.2s ease;
        }}

        .timeline-event:hover {{
            background-color: #f0f0f0;
        }}

        .timeline-time {{
            font-weight: bold;
            color: #667eea;
            min-width: 80px;
        }}

        .timeline-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            min-width: 80px;
            text-align: center;
        }}

        .badge-arrival {{ background: #d4edda; color: #155724; }}
        .badge-selection {{ background: #cce7ff; color: #004085; }}
        .badge-completion {{ background: #fff3cd; color: #856404; }}
        .badge-idle {{ background: #f8f9fa; color: #6c757d; }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .section {{
            animation: fadeIn 0.6s ease forwards;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Process Scheduler Report</h1>
            <p>{algorithm_display}{' - Quantum: ' + str(quantum) if algorithm == 'rr' else ''}</p>
            <p>{process_count} processes • Runtime: {run_for} time units</p>
        </div>

        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value">{stats['avg_wait_time']}</div>
                    <div class="stat-label">Avg Wait Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🔄</div>
                    <div class="stat-value">{stats['avg_turnaround_time']}</div>
                    <div class="stat-label">Avg Turnaround</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⚡</div>
                    <div class="stat-value">{stats['avg_response_time']}</div>
                    <div class="stat-label">Avg Response</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">📋 Process Statistics</h2>
                <table class="process-table">
                    <thead>
                        <tr>
                            <th>Process</th>
                            <th>Arrival Time</th>
                            <th>Burst Time</th>
                            <th>Wait Time</th>
                            <th>Turnaround Time</th>
                            <th>Response Time</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>"""

    # Add process rows
    finished_names = {p.name for p in finished_processes}
    all_processes_sorted = sorted(all_processes, key=lambda p: p.name)

    for p in all_processes_sorted:
        if p.name in finished_names:
            finished_p = next(fp for fp in finished_processes if fp.name == p.name)
            status = "✅ Completed"
            wait_time = finished_p.wait_time
            turnaround_time = finished_p.turnaround_time
            response_time = finished_p.response_time
        else:
            status = "❌ Did not finish"
            wait_time = "-"
            turnaround_time = "-"
            response_time = "-"

        html_template += f"""
                        <tr>
                            <td><strong>{p.name}</strong></td>
                            <td>{p.arrival}</td>
                            <td>{p.burst}</td>
                            <td>{wait_time}</td>
                            <td>{turnaround_time}</td>
                            <td>{response_time}</td>
                            <td>{status}</td>
                        </tr>"""

    html_template += f"""
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2 class="section-title">🕒 Timeline Events</h2>
                <div class="timeline">"""

    # Add timeline events
    for event in events:
        badge_class = f"badge-{event['type']}"
        badge_text = {
            'arrival': 'ARRIVAL',
            'selection': 'SELECTED',
            'completion': 'FINISHED',
            'idle': 'IDLE'
        }.get(event['type'], 'EVENT')

        html_template += f"""
                    <div class="timeline-event">
                        <div class="timeline-time">T{event['time']}</div>
                        <div class="timeline-badge {badge_class}">{badge_text}</div>
                        <div>{event['description']}</div>
                    </div>"""

    html_template += f"""
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Process Scheduler Simulator</p>
        </div>
    </div>

</body>
</html>"""

    # Write HTML file
    html_filename = filename.replace('.out', '.html')
    with open(html_filename, 'w') as f:
        f.write(html_template)

    return html_filename

def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: scheduler-gpt.py <input file>")
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

    # Always generate HTML report
    html_filename = generate_html_report(output_filename, process_count, algorithm, quantum, output, finished, run_for, processes)
    print(f"HTML report written to {html_filename}")

if __name__ == "__main__":
    main()
