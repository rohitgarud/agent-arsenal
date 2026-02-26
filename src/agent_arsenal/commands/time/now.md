---
name: now
description: Get current timestamp (alias for timestamp)
execution_type: executable
executable_type: python
executable_path: timestamp.handle_timestamp
args:
  - name: format
    type: string
    default: "%Y-%m-%d %H:%M:%S"
    description: strftime format string
  - name: tz
    type: string
    default: "local"
    description: Timezone name (UTC, America/New_York, local)
  - name: unix
    type: boolean
    default: false
    description: Return Unix timestamp
---

# Now Command

Get the current timestamp. This is an alias for the timestamp command.

## Usage

```bash
# Current time
arsenal time now

# Custom format
arsenal time now --format "%Y-%m-%d"

# Specific timezone
arsenal time now --tz UTC
```

## Arguments

- `--format`: strftime format string. Default: "%Y-%m-%d %H:%M:%S"
- `--tz`: Timezone name. Default: "local"
- `--unix`: Return Unix timestamp. Default: false