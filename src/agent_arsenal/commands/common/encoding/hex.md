---
name: hex
description: Encode or decode hexadecimal
execution_type: executable
executable_type: python
executable_path: hex.hex_encode
sandbox: false
args:
  - name: input
    type: string
    default: ""
    description: Text to encode/decode
  - name: decode
    type: boolean
    default: false
    description: Decode from hex instead of encoding
---

# Hex Encode/Decode

Encode text to hexadecimal or decode hex back to text.

## Usage

Encode to hex:
```bash
arsenal common encoding hex --input "hello"
```

Decode from hex:
```bash
arsenal common encoding hex --input "68656c6c6f" --decode
```