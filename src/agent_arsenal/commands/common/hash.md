---
name: hash
description: Compute cryptographic hashes (MD5, SHA256, SHA512)
execution_type: executable
executable_type: python
executable_path: hash.handle_hash
args:
  - name: algorithm
    type: string
    default: sha256
    description: Hash algorithm (md5, sha256, sha512)
  - name: input
    type: string
    default: ""
    description: Input string to hash (use - for stdin)
  - name: encoding
    type: string
    default: utf-8
    description: Input encoding (utf-8, latin-1, hex, base64)
---

# Hash Command

Compute cryptographic hashes of input strings.

## Usage

```bash
# Hash with SHA256 (default)
arsenal common hash --input "Hello, World!"

# Hash with MD5
arsenal common hash --algorithm md5 --input "Hello"

# Hash with SHA512
arsenal common hash --algorithm sha512 --input "Hello"

# Read from stdin
echo "Hello" | arsenal common hash --input -

# Hash a hex string
arsenal common hash --input "48656c6c6f" --encoding hex
```

## Arguments

- `--algorithm`: Hash algorithm - md5, sha256, or sha512. Default: sha256
- `--input`: Input string to hash. Use "-" to read from stdin. Default: (empty)
- `--encoding`: Input encoding - utf-8, latin-1, hex, or base64. Default: utf-8
