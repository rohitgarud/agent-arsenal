---
name: html_entity
description: Encode or decode HTML entities
execution_type: executable
executable_type: python
executable_path: html_entity.html_entity_encode
sandbox: false
args:
  - name: input
    type: string
    default: ""
    description: Text to encode/decode
  - name: decode
    type: boolean
    default: false
    description: Decode HTML entities instead of encoding
---

# HTML Entity Encode/Decode

Encode text to HTML entities or decode entities back to text.

## Usage

Encode to HTML entities:
```bash
arsenal common encoding html-entity --input "<hello>"
```

Decode HTML entities:
```bash
arsenal common encoding html-entity --input "&lt;hello&gt;" --decode
```