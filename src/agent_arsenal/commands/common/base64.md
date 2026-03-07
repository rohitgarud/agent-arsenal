---
name: base64
description: Encode or decode Base64
execution_type: executable
executable_type: python
executable_path: base64.handle_base64
sandbox: false
subcommands:
  - name: encode
    description: Encode input to Base64
  - name: decode
    description: Decode Base64 to plain text
args:
  - name: input
    type: string
    default: ""
    description: Input string (use - for stdin)
  - name: wrap
    type: integer
    default: 0
    description: Wrap output at this column (0 to disable)
---

# Base64 Command

Encode or decode Base64 strings.

## Usage

```bash
# Encode to Base64
arsenal common base64 encode --input "Hello, World!"

# Decode from Base64
arsenal common base64 decode --input "SGVsbG8="

# Read from stdin
echo "Hello" | arsenal common base64 encode

# Wrap output at 76 characters
arsenal common base64 encode --input "Hello" --wrap 76
```

## Arguments

- `--input`: Input string to process. Use "-" to read from stdin. Default: (empty)
- `--wrap`: Wrap output at this column. Use 0 to disable wrapping. Default: 0
