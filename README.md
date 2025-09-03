# Programming Assignment 1 Overview

In this project, we will implement three process scheduling algorithms in Python using ChatGPT as our primary coding assistant. Our goal is to simulate CPU scheduling for multiple processes and calculate key metrics such as turnaround time, waiting time, and response time.

### Scheduling Algorithms
- **FIFO (First In, First Out)**
- **Pre-emptive Shortest Job First (SJF)**
- **Round Robin (RR)** with a quantum parameter

### Components We Will Implement
- **Process Data Structure**: Includes arrival time, burst time, and status.  
- **Schedulers**: Functions for FIFO, SJF, and RR.  
- **Metrics**: Functions to compute turnaround, waiting, and response times.  
- **I/O Handling**:  
  - Input: Read `.in` files with process specifications and scheduling parameters.  
  - Output: Generate `.out` files showing events at each time tick, including arrivals, selections, completions, and idle times.  

---

# Deliverables

1. **Prompt History**  
   - Each of us must provide links to our ChatGPT conversation history.  
   - As a team, we will document how we derived the final code (best prompt, hybrid, or refinement).  

2. **Final Code**  
   - A single Python file: `scheduler-gpt.py`.  
   - We must include all team member names in comments at the top.  

3. **Final Report**  
   - A single Word or PDF file titled `Group-N Final Report.docx` (or `.pdf`).  
   - This will include:  
     - Team member names  
     - Links to all ChatGPT conversations  
     - Documentation of the prompt refinement process  
     - Our evaluation of ChatGPT’s output (see rubric)  

---

# Rubric Summary

### Correctness of Final Code (30 pts)
- 10 pts per algorithm (FIFO, SJF, RR).  
- Deductions for incorrect outputs.  

### Prompt and Conversation Submissions (10 pts)
- 4 pts for participation by all members.  
- 6 pts for quality and refinement shown in conversations.  

### Evaluation Report (60 pts)
- Correctness (10 pts): Does our code run correctly and handle errors?  
- Efficiency (10 pts): Is our code optimized?  
- Readability (10 pts): Is the code organized and easy to follow?  
- Completeness (10 pts): Does it handle edge cases and malformed input?  
- Innovation (10 pts): Did we bring new ideas or enhancements?  
- Overall Quality & Recommendation (10 pts): Our assessment of the AI-assisted coding experience.  

### Bonus (10 pts)
- Extra features like enhanced output, new scheduling algorithms, or GUI.

---

# Notes
- Input must be a `.in` file. Output will be written as `.out`.  
- Errors must follow the exact format specified in the instructions.  
- Any processes not finishing within runtime must be reported in the summary.  
