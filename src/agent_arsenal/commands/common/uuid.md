---
name: uuid
description: Generate UUIDs (version 4 or 7)
execution_type: executable
executable_type: python
executable_path: uuid.handle_uuid
args:
  - name: version
    type: integer
    default: 4
    description: UUID version (4 or 7)
  - name: uppercase
    type: boolean
    default: false
    description: Convert to uppercase
  - name: count
    type: integer
    default: 1
    description: Number of UUIDs to generate
aliases:
  - guid
---

# UUID Command

Generate universally unique identifiers (UUIDs).

## Usage

```bash
# Generate a UUID v4 (random)
arsenal common uuid

# Generate UUID v7 (time-ordered)
arsenal common uuid --version 7

# Generate multiple UUIDs
arsenal common uuid --count 5

# Uppercase output
arsenal common uuid --uppercase
```

## Arguments

- `--version`: UUID version - 4 (random) or 7 (time-ordered). Default: 4
- `--uppercase`: Convert output to uppercase. Default: false
- `--count`: Number of UUIDs to generate. Default: 1
