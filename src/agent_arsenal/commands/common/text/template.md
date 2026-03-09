---
name: template
description: Simple template substitution
execution_type: executable
executable_type: python
executable_path: template.handle_template
sandbox: false
args:
  - name: template
    type: string
    default: ""
    description: Template string with {{variable}} placeholders
  - name: values
    type: string
    default: ""
    description: JSON object with variable values
---

# Template

Simple template substitution using {{variable}} syntax.

## Usage

```bash
arsenal common text template --template "Hello {{name}}!" --values '{"name":"World"}'
arsenal common text template --template "{{a}} + {{b}} = {{c}}" --values '{"a":"1","b":"2","c":"3"}'
```