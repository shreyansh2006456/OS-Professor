import re
from collections import deque


# ============================================================
# QUESTION DETECTION
# ============================================================

def detect_topic(question):

    q = question.lower()

    # Page replacement
    if any(x in q for x in [
        "fifo page",
        "fifo replacement",
        "page replacement fifo",
        "lru page",
        "lru replacement",
        "optimal page",
        "optimal replacement",
        "page fault",
        "page faults",
        "reference string"
    ]):
        return "page_replacement"

    # CPU scheduling
    if any(x in q for x in [
        "fcfs",
        "first come first serve",
        "sjf",
        "shortest job first",
        "srtf",
        "shortest remaining",
        "round robin",
        "priority scheduling"
    ]):
        return "cpu_scheduling"

    # Banker's Algorithm
    if any(x in q for x in [
        "banker's",
        "bankers",
        "banker algorithm",
        "safe sequence",
        "available matrix",
        "need matrix"
    ]):
        return "bankers"

    # Paging
    if any(x in q for x in [
        "paging",
        "logical address",
        "physical address",
        "page number",
        "frame number",
        "page table"
    ]):
        return "paging"

    # Memory allocation
    if any(x in q for x in [
        "first fit",
        "best fit",
        "worst fit",
        "memory allocation"
    ]):
        return "memory_allocation"

    # Disk scheduling
    if any(x in q for x in [
        "sstf",
        "scan",
        "c-scan",
        "cscan",
        "look",
        "c-look",
        "clook",
        "disk scheduling",
        "disk head"
    ]):
        return "disk_scheduling"

    return None


# ============================================================
# CPU SCHEDULING
# ============================================================

def detect_scheduling_algorithm(question):

    q = question.lower()

    if "round robin" in q or re.search(r"\brr\b", q):
        return "round_robin"

    if "srtf" in q or "shortest remaining" in q:
        return "srtf"

    if "sjf" in q or "shortest job first" in q:
        return "sjf"

    if "priority" in q:
        return "priority"

    if "fcfs" in q or "first come first serve" in q:
        return "fcfs"

    return None


def extract_time_quantum(question):

    patterns = [
        r"time\s*quantum\s*[=: -]\s*(\d+)",
        r"quantum\s*[=: -]\s*(\d+)",
        r"\btq\s*[=: -]\s*(\d+)"
    ]

    q = question.lower()

    for pattern in patterns:

        match = re.search(pattern, q)

        if match:
            return int(match.group(1))

    return None


def extract_process_data(question):

    processes = []

    # P1 AT=0 BT=5
    pattern1 = re.compile(
        r"(P\d+).*?"
        r"(?:AT|Arrival\s*Time)\s*[=:]\s*(\d+).*?"
        r"(?:BT|Burst\s*Time)\s*[=:]\s*(\d+)",
        re.IGNORECASE
    )

    for match in pattern1.finditer(question):

        processes.append([
            match.group(1),
            int(match.group(2)),
            int(match.group(3))
        ])

    if processes:
        return processes

    # P1 0 5
    pattern2 = re.compile(
        r"(P\d+)\s+(\d+)\s+(\d+)",
        re.IGNORECASE
    )

    for match in pattern2.finditer(question):

        processes.append([
            match.group(1),
            int(match.group(2)),
            int(match.group(3))
        ])

    return processes


# ============================================================
# FCFS
# ============================================================

def solve_fcfs(processes):

    processes = sorted(
        processes,
        key=lambda x: (x[1], x[0])
    )

    time = 0
    result = []

    for name, arrival, burst in processes:

        if time < arrival:
            time = arrival

        start = time
        completion = start + burst

        turnaround = completion - arrival
        waiting = turnaround - burst
        response = start - arrival

        result.append({
            "process": name,
            "arrival": arrival,
            "burst": burst,
            "start": start,
            "completion": completion,
            "turnaround": turnaround,
            "waiting": waiting,
            "response": response
        })

        time = completion

    return result


# ============================================================
# SJF NON-PREEMPTIVE
# ============================================================

def solve_sjf(processes):

    remaining = [
        {
            "name": p[0],
            "arrival": p[1],
            "burst": p[2]
        }
        for p in processes
    ]

    time = 0
    completed = []

    while remaining:

        available = [
            p for p in remaining
            if p["arrival"] <= time
        ]

        if not available:

            time = min(
                p["arrival"]
                for p in remaining
            )

            continue

        current = min(
            available,
            key=lambda p: (
                p["burst"],
                p["arrival"],
                p["name"]
            )
        )

        start = time
        completion = time + current["burst"]

        turnaround = completion - current["arrival"]
        waiting = turnaround - current["burst"]
        response = start - current["arrival"]

        completed.append({
            "process": current["name"],
            "arrival": current["arrival"],
            "burst": current["burst"],
            "start": start,
            "completion": completion,
            "turnaround": turnaround,
            "waiting": waiting,
            "response": response
        })

        time = completion
        remaining.remove(current)

    return completed


# ============================================================
# SRTF
# ============================================================

def solve_srtf(processes):

    remaining = {
        p[0]: p[2]
        for p in processes
    }

    arrival = {
        p[0]: p[1]
        for p in processes
    }

    burst = {
        p[0]: p[2]
        for p in processes
    }

    completed = {}
    first_start = {}

    time = 0

    while len(completed) < len(processes):

        available = [
            p[0]
            for p in processes
            if p[1] <= time
            and remaining[p[0]] > 0
        ]

        if not available:

            future = [
                p[1]
                for p in processes
                if remaining[p[0]] > 0
                and p[1] > time
            ]

            if future:
                time = min(future)

            continue

        current = min(
            available,
            key=lambda name: (
                remaining[name],
                arrival[name],
                name
            )
        )

        if current not in first_start:
            first_start[current] = time

        remaining[current] -= 1
        time += 1

        if remaining[current] == 0:
            completed[current] = time

    result = []

    for name, arr, bt in processes:

        ct = completed[name]

        tat = ct - arr
        wt = tat - bt
        rt = first_start[name] - arr

        result.append({
            "process": name,
            "arrival": arr,
            "burst": bt,
            "completion": ct,
            "turnaround": tat,
            "waiting": wt,
            "response": rt
        })

    return result


# ============================================================
# PRIORITY NON-PREEMPTIVE
# ============================================================

def extract_priority_data(question):

    processes = []

    # P1 AT=0 BT=5 Priority=2
    pattern = re.compile(
        r"(P\d+).*?"
        r"(?:AT|Arrival\s*Time)\s*[=:]\s*(\d+).*?"
        r"(?:BT|Burst\s*Time)\s*[=:]\s*(\d+).*?"
        r"(?:Priority|P)\s*[=:]\s*(\d+)",
        re.IGNORECASE
    )

    for match in pattern.finditer(question):

        processes.append([
            match.group(1),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4))
        ])

    return processes


def solve_priority(processes):

    remaining = [
        {
            "name": p[0],
            "arrival": p[1],
            "burst": p[2],
            "priority": p[3]
        }
        for p in processes
    ]

    time = 0
    result = []

    while remaining:

        available = [
            p for p in remaining
            if p["arrival"] <= time
        ]

        if not available:

            time = min(
                p["arrival"]
                for p in remaining
            )

            continue

        current = min(
            available,
            key=lambda p: (
                p["priority"],
                p["arrival"],
                p["name"]
            )
        )

        start = time
        completion = start + current["burst"]

        tat = completion - current["arrival"]
        wt = tat - current["burst"]
        rt = start - current["arrival"]

        result.append({
            "process": current["name"],
            "arrival": current["arrival"],
            "burst": current["burst"],
            "priority": current["priority"],
            "start": start,
            "completion": completion,
            "turnaround": tat,
            "waiting": wt,
            "response": rt
        })

        time = completion
        remaining.remove(current)

    return result


# ============================================================
# ROUND ROBIN
# ============================================================

def solve_round_robin(processes, quantum):

    processes = sorted(
        processes,
        key=lambda x: (x[1], x[0])
    )

    remaining = {
        p[0]: p[2]
        for p in processes
    }

    arrival = {
        p[0]: p[1]
        for p in processes
    }

    burst = {
        p[0]: p[2]
        for p in processes
    }

    completion = {}
    first_start = {}

    ready_queue = deque()

    time = 0
    index = 0

    while index < len(processes) or ready_queue:

        if not ready_queue:

            time = max(
                time,
                processes[index][1]
            )

            while (
                index < len(processes)
                and processes[index][1] <= time
            ):

                ready_queue.append(
                    processes[index][0]
                )

                index += 1

        current = ready_queue.popleft()

        if current not in first_start:
            first_start[current] = time

        execution = min(
            quantum,
            remaining[current]
        )

        time += execution

        remaining[current] -= execution

        while (
            index < len(processes)
            and processes[index][1] <= time
        ):

            ready_queue.append(
                processes[index][0]
            )

            index += 1

        if remaining[current] > 0:

            ready_queue.append(current)

        else:

            completion[current] = time

    result = []

    for name, arr, bt in processes:

        ct = completion[name]

        tat = ct - arr
        wt = tat - bt
        rt = first_start[name] - arr

        result.append({
            "process": name,
            "arrival": arr,
            "burst": bt,
            "completion": ct,
            "turnaround": tat,
            "waiting": wt,
            "response": rt
        })

    return result


# ============================================================
# PAGE REPLACEMENT
# ============================================================

def extract_page_data(question):

    q = question.lower()

    # Number of frames
    frame_patterns = [
        r"(\d+)\s*(?:frames|frame)",
        r"frames?\s*[=:]\s*(\d+)",
        r"number\s+of\s+frames\s*[=:]\s*(\d+)"
    ]

    frames = None

    for pattern in frame_patterns:

        match = re.search(pattern, q)

        if match:

            frames = int(match.group(1))
            break

    # Reference string
    string_patterns = [
        r"reference\s*string\s*[=:]\s*([0-9\s,]+)",
        r"reference\s*string\s+([0-9\s,]+)",
        r"pages?\s*[=:]\s*([0-9\s,]+)"
    ]

    reference_string = None

    for pattern in string_patterns:

        match = re.search(pattern, q)

        if match:

            raw = match.group(1)

            reference_string = [
                int(x)
                for x in re.findall(
                    r"\d+",
                    raw
                )
            ]

            break

    return reference_string, frames


def solve_fifo(reference_string, frames_count):

    frames = []
    queue = []

    steps = []
    page_faults = 0
    page_hits = 0

    for page in reference_string:

        if page in frames:

            result = "HIT"
            page_hits += 1

        else:

            result = "PAGE FAULT"
            page_faults += 1

            if len(frames) < frames_count:

                frames.append(page)
                queue.append(page)

            else:

                old_page = queue.pop(0)

                index = frames.index(old_page)

                frames[index] = page

                queue.append(page)

        steps.append({
            "page": page,
            "frames": frames.copy(),
            "result": result
        })

    return {
        "algorithm": "FIFO",
        "steps": steps,
        "page_faults": page_faults,
        "page_hits": page_hits
    }


def solve_lru(reference_string, frames_count):

    frames = []

    recent = []

    steps = []
    page_faults = 0
    page_hits = 0

    for page in reference_string:

        if page in frames:

            result = "HIT"
            page_hits += 1

            recent.remove(page)
            recent.append(page)

        else:

            result = "PAGE FAULT"
            page_faults += 1

            if len(frames) < frames_count:

                frames.append(page)

            else:

                least_recent = recent.pop(0)

                index = frames.index(
                    least_recent
                )

                frames[index] = page

            recent.append(page)

        steps.append({
            "page": page,
            "frames": frames.copy(),
            "result": result
        })

    return {
        "algorithm": "LRU",
        "steps": steps,
        "page_faults": page_faults,
        "page_hits": page_hits
    }


def solve_optimal(reference_string, frames_count):

    frames = []

    steps = []
    page_faults = 0
    page_hits = 0

    for i, page in enumerate(reference_string):

        if page in frames:

            result = "HIT"
            page_hits += 1

        else:

            result = "PAGE FAULT"
            page_faults += 1

            if len(frames) < frames_count:

                frames.append(page)

            else:

                future = reference_string[i + 1:]

                distances = []

                for frame_page in frames:

                    if frame_page in future:

                        distance = future.index(
                            frame_page
                        )

                    else:

                        distance = float("inf")

                    distances.append(distance)

                replace_index = distances.index(
                    max(distances)
                )

                frames[replace_index] = page

        steps.append({
            "page": page,
            "frames": frames.copy(),
            "result": result
        })

    return {
        "algorithm": "Optimal",
        "steps": steps,
        "page_faults": page_faults,
        "page_hits": page_hits
    }


# ============================================================
# FORMAT PAGE REPLACEMENT
# ============================================================

def format_page_replacement(data):

    if not data["success"]:
        return data["message"]

    result = data["result"]

    algorithm = result["algorithm"]

    lines = []

    lines.append(
        f"Numerical Solution: {algorithm} Page Replacement"
    )

    lines.append("")

    lines.append(
        "Step | Page | Frames | Result"
    )

    lines.append(
        "-" * 55
    )

    for i, step in enumerate(
        result["steps"],
        start=1
    ):

        frame_text = " ".join(
            str(x)
            for x in step["frames"]
        )

        lines.append(
            f"{i:>4} | "
            f"{step['page']:>4} | "
            f"{frame_text:<15} | "
            f"{step['result']}"
        )

    lines.append("")

    lines.append(
        f"Total Page Faults = "
        f"{result['page_faults']}"
    )

    lines.append(
        f"Total Page Hits = "
        f"{result['page_hits']}"
    )

    return "\n".join(lines)


# ============================================================
# PAGING
# ============================================================

def solve_address_translation(
    logical_address,
    page_size,
    page_table
):

    page_number = logical_address // page_size

    offset = logical_address % page_size

    if page_number not in page_table:

        return {
            "success": False,
            "message": "Page number not present in page table."
        }

    frame_number = page_table[page_number]

    physical_address = (
        frame_number * page_size
    ) + offset

    return {
        "success": True,
        "page_number": page_number,
        "offset": offset,
        "frame_number": frame_number,
        "physical_address": physical_address
    }


# ============================================================
# MEMORY ALLOCATION
# ============================================================

def solve_memory_allocation(
    blocks,
    processes,
    method
):

    available = blocks.copy()

    allocation = []

    for process_size in processes:

        selected = -1

        if method == "first_fit":

            for i, block in enumerate(available):

                if block >= process_size:

                    selected = i
                    break

        elif method == "best_fit":

            candidates = [
                (i, block)
                for i, block in enumerate(
                    available
                )
                if block >= process_size
            ]

            if candidates:

                selected = min(
                    candidates,
                    key=lambda x: x[1]
                )[0]

        elif method == "worst_fit":

            candidates = [
                (i, block)
                for i, block in enumerate(
                    available
                )
                if block >= process_size
            ]

            if candidates:

                selected = max(
                    candidates,
                    key=lambda x: x[1]
                )[0]

        if selected == -1:

            allocation.append(None)

        else:

            allocation.append(selected)

            available[selected] -= process_size

    return {
        "allocation": allocation,
        "remaining_blocks": available
    }


# ============================================================
# MAIN NUMERICAL SOLVER
# ============================================================

def solve_os_numerical(question):

    topic = detect_topic(question)

    # ========================================================
    # PAGE REPLACEMENT
    # ========================================================

    if topic == "page_replacement":

        reference_string, frames = extract_page_data(
            question
        )

        if not reference_string:

            return {
                "success": False,
                "type": "page_replacement",
                "message": (
                    "I identified this as a page replacement "
                    "problem, but I could not find the "
                    "reference string."
                )
            }

        if not frames:

            return {
                "success": False,
                "type": "page_replacement",
                "message": (
                    "I identified this as a page replacement "
                    "problem, but I could not find the number "
                    "of frames."
                )
            }

        q = question.lower()

        if "lru" in q:

            result = solve_lru(
                reference_string,
                frames
            )

        elif "optimal" in q:

            result = solve_optimal(
                reference_string,
                frames
            )

        else:

            # Default for FIFO
            result = solve_fifo(
                reference_string,
                frames
            )

        return {
            "success": True,
            "type": "page_replacement",
            "result": result
        }

    # ========================================================
    # CPU SCHEDULING
    # ========================================================

    if topic == "cpu_scheduling":

        algorithm = detect_scheduling_algorithm(
            question
        )

        if not algorithm:

            return {
                "success": False,
                "type": "scheduling",
                "message": (
                    "I could not identify the CPU scheduling "
                    "algorithm."
                )
            }

        processes = extract_process_data(
            question
        )

        if not processes:

            return {
                "success": False,
                "type": "scheduling",
                "message": (
                    "I identified this as a CPU scheduling "
                    "problem, but I could not clearly extract "
                    "the process values."
                )
            }

        if algorithm == "fcfs":

            result = solve_fcfs(
                processes
            )

        elif algorithm == "sjf":

            result = solve_sjf(
                processes
            )

        elif algorithm == "srtf":

            result = solve_srtf(
                processes
            )

        elif algorithm == "round_robin":

            quantum = extract_time_quantum(
                question
            )

            if quantum is None:

                return {
                    "success": False,
                    "type": "round_robin",
                    "message": (
                        "I identified this as a Round Robin "
                        "problem, but the time quantum was "
                        "not provided."
                    )
                }

            result = solve_round_robin(
                processes,
                quantum
            )

        elif algorithm == "priority":

            priority_processes = extract_priority_data(
                question
            )

            if not priority_processes:

                return {
                    "success": False,
                    "type": "priority",
                    "message": (
                        "Priority scheduling was detected, "
                        "but priority values could not "
                        "be extracted."
                    )
                }

            result = solve_priority(
                priority_processes
            )

        else:

            return {
                "success": False,
                "type": "scheduling",
                "message": (
                    f"{algorithm} is not currently supported."
                )
            }

        return {
            "success": True,
            "type": "scheduling",
            "algorithm": algorithm,
            "result": result
        }

    # ========================================================
    # NO SOLVER
    # ========================================================

    return {
        "success": False,
        "type": "unknown",
        "message": (
            "No specialized numerical solver was detected."
        )
    }


# ============================================================
# FORMAT SCHEDULING RESULT
# ============================================================

def format_scheduling_result(data):

    if not data["success"]:
        return data["message"]

    result = data["result"]

    names = {
        "fcfs": "FCFS",
        "sjf": "Shortest Job First (SJF)",
        "srtf": "Shortest Remaining Time First (SRTF)",
        "round_robin": "Round Robin",
        "priority": "Priority Scheduling"
    }

    algorithm_name = names.get(
        data["algorithm"],
        data["algorithm"]
    )

    output = []

    output.append(
        f"Numerical Solution: {algorithm_name}"
    )

    output.append("")

    output.append(
        "Process | AT | BT | CT | TAT | WT | RT"
    )

    output.append(
        "-" * 55
    )

    total_wt = 0
    total_tat = 0

    for row in result:

        output.append(
            f"{row['process']} | "
            f"{row['arrival']} | "
            f"{row['burst']} | "
            f"{row['completion']} | "
            f"{row['turnaround']} | "
            f"{row['waiting']} | "
            f"{row['response']}"
        )

        total_wt += row["waiting"]
        total_tat += row["turnaround"]

    count = len(result)

    average_wt = total_wt / count
    average_tat = total_tat / count

    output.append("")

    output.append(
        f"Average Waiting Time = "
        f"{average_wt:.2f}"
    )

    output.append(
        f"Average Turnaround Time = "
        f"{average_tat:.2f}"
    )

    return "\n".join(output)


# ============================================================
# UNIVERSAL FORMATTER
# ============================================================

def format_numerical_result(data):

    if not data["success"]:

        return data["message"]

    if data["type"] == "page_replacement":

        return format_page_replacement(
            data
        )

    if data["type"] == "scheduling":

        return format_scheduling_result(
            data
        )

    return data.get(
        "message",
        "Numerical solution generated."
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("OS NUMERICAL SOLVER TEST")
    print("=" * 60)

    test = (
        "Numerical on FIFO page replacement. "
        "Reference string: 1 2 3 1 4 5 2 1. "
        "Number of frames: 3"
    )

    result = solve_os_numerical(test)

    print(
        format_numerical_result(result)
    )