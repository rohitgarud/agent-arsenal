---
name: word_count
description: Count words, characters, and lines in text
execution_type: executable
executable_type: python
executable_path: word_count.handle_word_count
sandbox: false
args:
  - name: text
    type: string
    default: ""
    description: Text to count (use - for stdin)
  - name: chars
    type: boolean
    default: false
    description: Include character count
  - name: lines
    type: boolean
    default: false
    description: Include line count
---

# Word Count

Count words, characters, and lines in text.

## Usage

```bash
arsenal common text word-count --text "Hello world"
arsenal common text word-count --text "Hello world" --chars --lines
echo "Hello world" | arsenal common text word-count --text "-"
```