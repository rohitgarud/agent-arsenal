---
name: diff
description: Compare two texts and show differences
execution_type: executable
executable_type: python
executable_path: diff.handle_diff
sandbox: false
args:
  - name: text1
    type: string
    default: ""
    description: First text (use - for stdin)
  - name: text2
    type: string
    default: ""
    description: Second text (use - for stdin)
  - name: context
    type: integer
    default: 3
    description: Number of context lines to show
---

# Diff

Compare two texts and show differences.

## Usage

```bash
arsenal common text diff --text1 "Hello world" --text2 "Hello there"
echo -e "Hello\nworld" | arsenal common text diff --text1 "-" --text2 "Hello\nworld"
```