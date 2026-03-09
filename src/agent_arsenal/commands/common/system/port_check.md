---
name: port_check
description: Check if a network port is open
execution_type: executable
executable_type: python
executable_path: port_check.handle_port_check
sandbox: false
args:
  - name: port
    type: integer
    default: 80
    description: Port number to check
  - name: host
    type: string
    default: "localhost"
    description: Host to check
  - name: timeout
    type: integer
    default: 3
    description: Connection timeout in seconds
---

# Port Check

Check if a network port is open on a host.

## Usage

```bash
arsenal common system port-check --port 8080
arsenal common system port-check --port 443 --host "example.com"
arsenal common system port-check --port 22 --host "localhost" --timeout 5
```