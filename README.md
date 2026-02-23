# Agent Arsenal

A global CLI tool for coding agents to use in development.

## Installation

### Install Globally (Editable Mode)

For development, install the tool globally in editable mode:

```bash
cd agent-arsenal
uv tool install . --editable
```

This allows you to:
- Run `arsenal` from anywhere on your system
- Make changes to the code and see them immediately without reinstalling

### Install Globally (Standard)

For production use:

```bash
cd agent-arsenal
uv tool install .
```

### Uninstall

```bash
uv tool uninstall agent-arsenal
```

### Update Installation (Editable Mode)

If you've made changes and need to refresh:

```bash
uv tool install . --editable --force
```

## Usage

Once installed, you can run the CLI from anywhere:

```bash
# Show help
arsenal --help

# Show version
arsenal --version
```

## Development

### Project Structure

```
agent-arsenal/
├── src/
│   └── agent_arsenal/
│       ├── __init__.py      # Package initialization
│       └── main.py          # CLI entry point
│       └── commands/        # Markdown-based commands
├── pyproject.toml           # Project configuration
├── README.md               # This file
└── .gitignore             # Git ignore patterns
```

### Adding New Commands

Commands are stored as markdown files in `src/agent_arsenal/commands/`.

1. Create a new `.md` file in a category folder (e.g., `src/agent_arsenal/commands/mygroup/mycmd.md`)
2. Add YAML frontmatter with metadata
3. Add instructions in markdown

## Requirements

- Python >= 3.12
- uv package manager

## Dependencies

- **typer** - CLI framework with type hints
- **rich** - Beautiful terminal output
- **pydantic** - Data validation
- **pyyaml** - YAML parsing

## License

Add your license here.
