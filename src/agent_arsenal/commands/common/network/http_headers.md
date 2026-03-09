---
name: http_headers
description: Fetch HTTP headers from a URL
execution_type: executable
executable_type: python
executable_path: http_headers.get_headers
sandbox: false
args:
  - name: url
    type: string
    required: true
    description: URL to fetch headers from
  - name: follow_redirects
    type: boolean
    default: true
    description: Follow redirects
---

# HTTP Headers

Fetch HTTP headers from a URL.

## Usage

```bash
arsenal common network http_headers --url "https://example.com"
```