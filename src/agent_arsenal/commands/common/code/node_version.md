---
name: node_version
description: Get the current Node.js version
execution_type: executable
executable_type: node
executable_inline: console.log(process.version)
args:
  - name: full
    type: boolean
    description: Show full version info (including platform, arch)
    required: false
    default: false
---
Get the Node.js version.

## Usage

```bash
arsenal common code node_version
```

## Arguments

- `full` (optional): If true, shows full version info including platform and architecture

## Example Output

```
v22.11.0
```
