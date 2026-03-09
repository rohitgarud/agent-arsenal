---
name: punycode
description: Encode or decode punycode (internationalized domain names)
execution_type: executable
executable_type: python
executable_path: punycode.punycode_encode
sandbox: false
args:
  - name: input
    type: string
    default: ""
    description: Domain name to encode/decode
  - name: decode
    type: boolean
    default: false
    description: Decode punycode instead of encoding
---

# Punycode Encode/Decode

Encode or decode internationalized domain names (IDN) using punycode.

## Usage

Encode to punycode:
```bash
arsenal common encoding punycode --input "münchen.de"
```

Decode from punycode:
```bash
arsenal common encoding punycode --input "xn--mnchen-3ya.de" --decode
```