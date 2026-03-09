---
name: url_safe_base64
description: URL-safe base64 encoding/decoding
execution_type: executable
executable_type: python
executable_path: url_safe_base64.url_safe_base64_encode
sandbox: false
args:
  - name: input
    type: string
    default: ""
    description: Text to encode/decode
  - name: decode
    type: boolean
    default: false
    description: Decode from base64 instead of encoding
---

# URL-Safe Base64 Encode/Decode

Encode or decode using URL-safe base64 (replaces + with - and / with _).

## Usage

Encode to URL-safe base64:
```bash
arsenal common encoding url-safe-base64 --input "hello+world"
```

Decode from URL-safe base64:
```bash
arsenal common encoding url-safe-base64 --input "aGVsbG8td29ybGQ" --decode
```