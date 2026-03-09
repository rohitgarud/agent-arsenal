---
name: relative_time
description: Calculate relative time from now
execution_type: executable
executable_type: python
executable_path: relative_time.get_relative_time
sandbox: false
args:
  - name: date
    type: string
    required: true
    description: Date string (YYYY-MM-DD or ISO format)
  - name: from_date
    type: string
    default: ""
    description: Reference date (defaults to now)
---

# Relative Time

Calculate relative time from now or a reference date.

## Usage

```bash
arsenal common datetime relative_time --date "2026-01-01"
```

From specific date:
```bash
arsenal common datetime relative_time --date "2026-03-09" --from_date "2026-01-01"
```