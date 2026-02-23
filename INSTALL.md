# Agent Arsenal - Installation & Usage Guide

## Project Structure Created

```
agent-arsenal/
├── src/
│   └── agent_arsenal/
│       ├── __init__.py          # Package version and metadata
│       ├── main.py              # CLI entry point with Typer
│       └── commands/            # Markdown-based commands (Hierarchical)
├── pyproject.toml               # Project config with console script
├── README.md                    # Full documentation
├── .gitignore                   # Git ignore patterns
├── .python-version              # Python version (3.12)
└── uv.lock                      # Dependency lock file
```

## Installation Commands

### 1. Install Globally in Editable Mode (Development)

```bash
cd /home/rohitgarud/agent-arsenal
uv tool install . --editable
```

**Benefits:**
- Changes to code are immediately reflected
- No need to reinstall after editing files
- Can run `arsenal` from anywhere

### 2. Install Globally (Production)

```bash
cd /home/rohitgarud/agent-arsenal
uv tool install .
```

### 3. Verify Installation

```bash
arsenal --help
arsenal --version
```

### 4. Update/Reinstall (if needed)

```bash
uv tool install . --editable --force
```

### 5. Uninstall

```bash
uv tool uninstall agent-arsenal
```

## Development Workflow

### Local Testing (without global install)

```bash
cd /home/rohitgarud/agent-arsenal
uv run arsenal --help
uv run arsenal --version
```

### Adding New Commands

Commands are automatically discovered from `src/agent_arsenal/commands/`.

1. Create a subfolder for a group (e.g., `src/agent_arsenal/commands/db/`)
2. Add `info.md` in the subfolder for group description.
3. Add `<command_name>.md` for individual commands.

## Current Features

✅ Global CLI tool installable via `uv tool install`
✅ `arsenal` command name (short and concise)
✅ Typer framework for rich CLI experience
✅ Rich library for beautiful terminal output
✅ Version command (`--version`)
✅ Help system (`--help`)
✅ Editable installation support
✅ Hierarchical folder-based command discovery
