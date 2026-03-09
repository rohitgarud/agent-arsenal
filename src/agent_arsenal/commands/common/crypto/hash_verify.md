---
name: hash_verify
description: Generate and verify hash digests
execution_type: executable
executable_type: python
executable_path: hash_verify.hash_verify
sandbox: false
args:
  - name: text
    type: string
    required: true
    description: Text to hash
  - name: algorithm
    type: string
    default: sha256
    description: Hash algorithm (md5, sha1, sha256, sha512)
  - name: verify
    type: string
    default: ""
    description: Expected hash to verify against
---

# Hash Generator/Verifier

Generate hash digests or verify against an expected hash.

## Usage

Generate hash:
```bash
arsenal common crypto hash_verify --text "hello world"
```

Verify hash:
```bash
arsenal common crypto hash_verify --text "hello world" --verify "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
```