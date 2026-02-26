---
name: convert
description: Convert time between timezones
execution_type: executable
executable_type: python
executable_path: time_convert.handle_time_convert
args:
  - name: time
    type: string
    default: ""
    description: "Time string to convert (default: now)"
  - name: from_tz
    type: string
    default: "UTC"
    description: Source timezone
  - name: to_tz
    type: string
    default: "local"
    description: Target timezone
  - name: format
    type: string
    default: "%Y-%m-%d %H:%M:%S"
    description: Output format string
---

# Convert Command

Convert time between different timezones.

## Usage

```bash
# Convert current UTC time to local
arsenal time convert

# Convert specific time
arsenal time convert --time "2024-01-15 10:00:00" --from_tz UTC --to_tz "America/New_York"

# Different output format
arsenal time convert --time "10:00" --from_tz "Europe/London" --to_tz "Asia/Tokyo" --format "%H:%M"
```

## Arguments

- `--time`: Time string to convert. Default: current time
- `--from_tz`: Source timezone. Default: UTC
- `--to_tz`: Target timezone. Default: local
- `--format`: Output format string. Default: "%Y-%m-%d %H:%M:%S"