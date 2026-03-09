---
name: disk_usage
description: Show disk usage information
execution_type: executable
executable_type: python
executable_path: disk_usage.handle_disk_usage
sandbox: false
args:
  - name: path
    type: string
    default: "."
    description: Path to check disk usage for
  - name: human
    type: boolean
    default: true
    description: Human-readable sizes (KB, MB, GB)
---

# Disk Usage

Show disk usage information for a path.

## Usage

```bash
arsenal common system disk-usage
arsenal common system disk-usage --path "/home"
arsenal common system disk-usage --path "." --human
```