---
name: process_list
description: List running processes
execution_type: executable
executable_type: python
executable_path: process_list.handle_process_list
sandbox: false
args:
  - name: limit
    type: integer
    default: 10
    description: Maximum number of processes to show
  - name: user
    type: string
    default: ""
    description: Filter by user (optional)
---

# Process List

List running processes on the system.

## Usage

```bash
arsenal common system process-list
arsenal common system process-list --limit 20
arsenal common system process-list --user root
```