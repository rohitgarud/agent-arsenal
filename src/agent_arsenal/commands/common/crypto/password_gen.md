---
name: password_gen
description: Generate a secure random password
execution_type: executable
executable_type: python
executable_path: password_gen.generate_password
sandbox: false
args:
  - name: length
    type: integer
    default: 16
    description: Password length (8-128)
  - name: use_special
    type: boolean
    default: true
    description: Include special characters (!@#$%^&*)
  - name: use_digits
    type: boolean
    default: true
    description: Include digits (0-9)
  - name: use_uppercase
    type: boolean
    default: true
    description: Include uppercase letters
---

# Password Generator

Generate a secure random password.

## Usage

```bash
arsenal common crypto password_gen
```

Custom length:
```bash
arsenal common crypto password_gen --length 24
```

No special characters:
```bash
arsenal common crypto password_gen --use_special false
```