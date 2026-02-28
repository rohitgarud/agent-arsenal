---
name: jwt
description: Decode JWT tokens (read-only)
execution_type: executable
executable_type: python
executable_path: jwt.handle_jwt
args:
  - name: token
    type: string
    default: ""
    description: JWT token to decode
  - name: part
    type: string
    default: all
    description: Which part to show (header, payload, signature, all)
---

# JWT Command

Decode JWT tokens and display their contents.

Note: This command only DECODES tokens for inspection. It does NOT verify signatures or encode tokens (for security reasons).

## Usage

```bash
# Decode full token
arsenal code jwt --token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Show only header
arsenal code jwt --token "<token>" --part header

# Show only payload
arsenal code jwt --token "<token>" --part payload
```

## Arguments

- `--token`: JWT token to decode. Default: (empty)
- `--part`: Which part to show - header, payload, signature, or all. Default: all
