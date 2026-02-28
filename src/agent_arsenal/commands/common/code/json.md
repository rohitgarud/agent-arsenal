---
name: json
description: Format, validate, or minify JSON
execution_type: executable
executable_type: python
executable_path: json.handle_json
args:
  - name: input
    type: string
    default: ""
    description: Input JSON string (use - for stdin)
  - name: indent
    type: integer
    default: 2
    description: Indentation spaces (0 for minified)
  - name: minify
    type: boolean
    default: false
    description: Minify output (overrides indent)
  - name: validate
    type: boolean
    default: false
    description: Only validate, no output
---

# JSON Command

Format, validate, or minify JSON.

## Usage

```bash
# Pretty print with 2-space indent
arsenal code json --input '{"key":"value"}'

# Minify JSON
arsenal code json --input '{"key":"value"}' --minify

# Custom indent
arsenal code json --input '{"key":"value"}' --indent 4

# Validate only
arsenal code json --input '{"key":"value"}' --validate

# Read from stdin
echo '{"key":"value"}' | arsenal code json
```

## Arguments

- `--input`: Input JSON string. Use "-" to read from stdin. Default: (empty)
- `--indent`: Indentation spaces. Use 0 for minified. Default: 2
- `--minify`: Output minified JSON (ignores indent). Default: false
- `--validate`: Only validate JSON, no output. Default: false
