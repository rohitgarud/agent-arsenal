---
name: timestamp
description: Get current timestamp with optional format and timezone
execution_type: executable
executable_type: python
executable_path: timestamp.handle_timestamp
sandbox: false
aliases:
  - now
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

# Timestamp Command

Get the current timestamp with customizable format and timezone.

## Usage

```bash
# Default timestamp
arsenal common time timestamp

# Or use 'now' alias
arsenal common time now

# Custom format
arsenal common time timestamp --format "%Y-%m-%d"

# Specific timezone
arsenal common time timestamp --tz UTC
arsenal common time timestamp --tz "America/New_York"

# Unix timestamp
arsenal common time timestamp --unix
```

## Arguments

- `--format`: strftime format string (default: "%Y-%m-%d %H:%M:%S")
- `--tz`: Timezone name (default: "local", use IANA names like "UTC")
- `--unix`: Return Unix timestamp instead of formatted string
