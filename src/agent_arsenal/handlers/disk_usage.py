"""Disk usage handler."""

import os
import shutil


def handle_disk_usage(path: str = ".", human: bool = True) -> str:
    """Show disk usage information.

    Args:
        path: Path to check disk usage for
        human: Human-readable sizes (KB, MB, GB)

    Returns:
        Disk usage information
    """
    try:
        # Resolve the path
        abs_path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(abs_path):
            return f"Error: Path '{path}' does not exist"

        # Get disk usage
        stat = shutil.disk_usage(abs_path)

        total = stat.total
        used = stat.used
        free = stat.free
        percent = (used / total) * 100

        # Format sizes
        if human:
            total_str = _human_size(total)
            used_str = _human_size(used)
            free_str = _human_size(free)
        else:
            total_str = f"{total} bytes"
            used_str = f"{used} bytes"
            free_str = f"{free} bytes"

        # Build output
        lines = [
            f"Disk usage for: {abs_path}",
            f"Total: {total_str}",
            f"Used:  {used_str} ({percent:.1f}%)",
            f"Free:  {free_str}",
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


def _human_size(size: float) -> str:
    """Convert bytes to human-readable size.

    Args:
        size: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"
