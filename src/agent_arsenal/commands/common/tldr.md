---
name: tldr
description: Get simplified man pages for CLI commands
execution_type: executable
executable_type: python
executable_path: tldr.handle_tldr
sandbox: false
args:
  - name: command
    type: string
    description: CLI command to look up (e.g., docker, kubectl, git)
---

# tldr Command

Get simplified, practical help pages for command-line tools.

## Usage

```bash
# Get help for docker
arsenal common tldr docker

# Get help for kubectl
arsenal common tldr kubectl

# Get help for git
arsenal common tldr git
```

## Arguments

- `--command`: CLI command name to look up (required)