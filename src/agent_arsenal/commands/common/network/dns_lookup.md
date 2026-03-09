---
name: dns_lookup
description: Perform DNS lookup for a domain
execution_type: executable
executable_type: python
executable_path: dns_lookup.dns_lookup
sandbox: false
args:
  - name: domain
    type: string
    required: true
    description: Domain name to lookup
  - name: record_type
    type: string
    default: A
    description: DNS record type (A, AAAA, MX, TXT, CNAME, NS)
---

# DNS Lookup

Perform DNS lookups for domains.

## Usage

```bash
arsenal common network dns_lookup --domain "example.com"
```

MX records lookup:
```bash
arsenal common network dns_lookup --domain "example.com" --record_type MX
```