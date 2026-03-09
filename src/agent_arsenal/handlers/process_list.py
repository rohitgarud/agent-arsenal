"""Process list handler."""

import os


def handle_process_list(limit: int = 10, user: str = "") -> str:
    """List running processes.

    Args:
        limit: Maximum number of processes to show
        user: Filter by user (optional)

    Returns:
        Process list as string
    """
    try:
        # Read /proc to get process info (Linux)
        processes = []
        proc_path = "/proc"

        for pid in os.listdir(proc_path):
            if not pid.isdigit():
                continue

            try:
                # Get process status
                status_path = os.path.join(proc_path, pid, "status")
                with open(status_path) as f:
                    status = f.read()

                proc_info = {"pid": pid}

                for line in status.split("\n"):
                    if line.startswith("Name:"):
                        proc_info["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Uid:"):
                        proc_info["uid"] = line.split(":", 1)[1].strip().split()[0]
                    elif line.startswith("State:"):
                        proc_info["state"] = line.split(":", 1)[1].strip()

                # Get user name if needed
                if user:
                    try:
                        import pwd

                        proc_info["username"] = pwd.getpwuid(
                            int(proc_info["uid"])
                        ).pw_name
                    except (ImportError, KeyError):
                        proc_info["username"] = proc_info["uid"]

                    if proc_info["username"] != user:
                        continue
                else:
                    try:
                        import pwd

                        proc_info["username"] = pwd.getpwuid(
                            int(proc_info["uid"])
                        ).pw_name
                    except (ImportError, KeyError):
                        proc_info["username"] = proc_info["uid"]

                processes.append(proc_info)

            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue

        # Sort by PID
        processes.sort(key=lambda x: int(x["pid"]), reverse=True)

        # Limit results
        processes = processes[:limit]

        # Format output
        if not processes:
            return "No processes found"

        lines = [f"{'PID':<8} {'USER':<15} {'NAME':<20} {'STATE'}" for _ in range(1)]
        lines.append("-" * 60)

        for proc in processes:
            name = proc.get("name", "unknown")[:20]
            user = proc.get("username", "unknown")[:15]
            state = proc.get("state", "unknown")[:10]
            lines.append(f"{proc['pid']:<8} {user:<15} {name:<20} {state}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"
