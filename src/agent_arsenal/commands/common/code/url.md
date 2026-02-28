---
name: url
description: URL encode or decode strings
execution_type: executable
executable_type: python
executable_path: url.handle_url
args:
  - name: mode
    type: string
    default: encode
    description: Mode (encode or decode)
  - name: input
    type: string
    default: ""
    description: Input string to process
---

# URL Command

URL encode or decode strings.

## Usage

```bash
# URL encode
arsenal code url --input "Hello World!"

# URL decode
arsenal code url --mode decode --input "Hello%20World%21"
```

## Arguments

- `--mode`: Operation mode - encode or decode. Default: encode
- `--input`: Input string to process. Default: (empty)
