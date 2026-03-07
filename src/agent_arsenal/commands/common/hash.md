---
name: hash
description: Compute cryptographic hashes (MD5, SHA256, SHA512)
execution_type: executable
executable_type: python
executable_path: hash.handle_hash
sandbox: false
subcommands:
  - name: md5
    description: Hash using MD5
  - name: sha1
    description: Hash using SHA1
  - name: sha256
    description: Hash using SHA256 (default)
  - name: sha512
    description: Hash using SHA512
args:
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
arsenal common hash sha256 --input "Hello, World!"

# Hash with MD5
arsenal common hash md5 --input "Hello"

# Hash with SHA1
arsenal common hash sha1 --input "Hello"

# Hash with SHA512
arsenal common hash sha512 --input "Hello"

# Read from stdin
echo "Hello" | arsenal common hash sha256 --input -

# Hash a hex string
arsenal common hash sha256 --input "48656c6c6f" --encoding hex
```

## Arguments

- `--input`: Input string to hash. Use "-" to read from stdin. Default: (empty)
- `--encoding`: Input encoding - utf-8, latin-1, hex, or base64. Default: utf-8
