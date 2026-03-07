---
name: json
description: Format, validate, or minify JSON
execution_type: executable
executable_type: python
executable_path: json.handle_json
sandbox: false
subcommands:
  - name: format
    description: Format JSON with indentation
  - name: validate
    description: Validate JSON only
  - name: minify
    description: Minify JSON output
args:
  - name: input
    type: string
    default: ""
    description: Input JSON string (use - for stdin)
  - name: indent
    type: integer
    default: 2
    description: Indentation spaces (0 for minified)
---

# JSON Command

Format, validate, or minify JSON.

## Usage

```bash
# Pretty print with 2-space indent
arsenal code json format --input '{"key":"value"}'

# Minify JSON
arsenal code json minify --input '{"key":"value"}'

# Custom indent
arsenal code json format --input '{"key":"value"}' --indent 4

# Validate only
arsenal code json validate --input '{"key":"value"}'

# Read from stdin
echo '{"key":"value"}' | arsenal code json format
```

## Arguments

- `--input`: Input JSON string. Use "-" to read from stdin. Default: (empty)
- `--indent`: Indentation spaces. Use 0 for minified. Default: 2
