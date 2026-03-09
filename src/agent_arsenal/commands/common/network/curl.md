---
name: curl
description: Make HTTP requests with curl-like functionality
execution_type: executable
executable_type: python
executable_path: curl.http_request
sandbox: false
args:
  - name: url
    type: string
    required: true
    description: URL to request
  - name: method
    type: string
    default: GET
    description: HTTP method (GET, POST, PUT, DELETE)
  - name: data
    type: string
    default: ""
    description: Request body data
  - name: headers
    type: string
    default: ""
    description: Custom headers (JSON format)
---

# HTTP Request

Make HTTP requests similar to curl.

## Usage

```bash
arsenal common network curl --url "https://example.com"
```

POST request with data:
```bash
arsenal common network curl --url "https://api.example.com/data" --method POST --data '{"key":"value"}'
```