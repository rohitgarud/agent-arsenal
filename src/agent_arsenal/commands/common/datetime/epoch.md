---
name: epoch
description: Convert epoch timestamps to/from datetime
execution_type: executable
executable_type: python
executable_path: epoch.epoch_converter
sandbox: false
args:
  - name: value
    type: string
    required: true
    description: Epoch timestamp or datetime string
  - name: to_epoch
    type: boolean
    default: true
    description: Convert datetime to epoch (false = epoch to datetime)
  - name: tz
    type: string
    default: UTC
    description: Timezone (UTC, local, or IANA timezone)
---

# Epoch Converter

Convert epoch timestamps to/from datetime.

## Usage

Datetime to epoch:
```bash
arsenal common datetime epoch --value "2026-03-09 12:00:00"
```

Epoch to datetime:
```bash
arsenal common datetime epoch --value "1709990400" --to_epoch false
```