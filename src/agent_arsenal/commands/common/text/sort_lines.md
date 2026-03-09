---
name: sort_lines
description: Sort lines of text alphabetically or numerically
execution_type: executable
executable_type: python
executable_path: sort_lines.handle_sort_lines
sandbox: false
args:
  - name: text
    type: string
    default: ""
    description: Text to sort (use - for stdin)
  - name: reverse
    type: boolean
    default: false
    description: Sort in reverse order
  - name: numeric
    type: boolean
    default: false
    description: Sort numerically instead of alphabetically
  - name: unique
    type: boolean
    default: false
    description: Remove duplicate lines
---

# Sort Lines

Sort lines of text alphabetically or numerically.

## Usage

```bash
arsenal common text sort-lines --text "banana\napple\ncherry"
arsenal common text sort-lines --text "3\n1\n2" --numeric
arsenal common text sort-lines --text "a\nb\na" --unique
```