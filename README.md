# Agent Arsenal

A global CLI tool for coding agents to use in development. Provides a hierarchical command system with built-in utilities for common development tasks.

## Quick Start

```bash
# Install globally (recommended - from PyPI)
uv tool install agent-arsenal

# Or using pip
pip install agent-arsenal

# Show help
arsenal --help

# Generate a UUID
arsenal common uuid

# Alias for uuid
arsenal common guid

# Compute SHA256 hash
arsenal common hash --input "mysecret"

# Encode to Base64
arsenal common base64 --input "hello world"

# Format/validate JSON
arsenal common code json --input '{"key":"value"}'

# Get current timestamp
arsenal common time now

# Store a value
arsenal state set mykey "myvalue"

# Retrieve stored value
arsenal state get mykey

# List external directories
arsenal config external-dir list

# Watch for command changes
arsenal watch
```

## Installation

### Recommended: Install from PyPI

The easiest way to install agent-arsenal is directly from PyPI:

```bash
# Using uv (recommended)
uv tool install agent-arsenal

# Or using pip (global scope)
pip install agent-arsenal
```

### Install for Development (Editable Mode)

If you want to contribute or modify the source code, install in editable mode:

```bash
cd agent-arsenal
uv tool install . --editable
```

This allows you to:
- Run `arsenal` from anywhere on your system
- Make changes to the code and see them immediately without reinstalling

### Install from Source (Standard)

For production use from source:

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

## Command Reference

### Root Commands

| Command | Description |
|---------|-------------|
| `watch [--debounce MS]` | Watch .md files for changes and auto-reload |

### Common Commands

| Command | Description |
|---------|-------------|
| `common uuid` / `common guid` | Generate UUID (v4 random or v7 time-ordered) |
| `common hash --input TEXT [--algorithm md5\|sha256\|sha512]` | Compute hash |
| `common base64 --input TEXT [--mode encode\|decode]` | Base64 encode/decode |
| `common code json --input TEXT [--mode format\|validate\|minify]` | JSON utilities |
| `common code url --input TEXT [--mode encode\|decode]` | URL encode/decode |
| `common code jwt --token TEXT [--part header\|payload]` | Decode JWT |
| `common code node_version` | Get Node.js version |
| `common time now` / `common timestamp` | Get current timestamp |
| `common time convert --time TEXT --from-tz TZ --to-tz TZ` | Timezone conversion |

### Config Commands

| Command | Description |
|---------|-------------|
| `config external-dir add <path>` | Add external command directory |
| `config external-dir remove <path>` | Remove directory |
| `config external-dir list` | List all directories |
| `config sandbox show` | Display sandbox config |
| `config sandbox set-timeout <seconds>` | Set timeout |
| `config sandbox set-permissions [--allow-read PATHS] [--allow-write PATHS] [--allow-net] [--allow-env VARS] [--allow-run]` | Set permissions |
| `config sandbox enable` | Enable sandbox |
| `config sandbox disable` | Disable sandbox |

### State Commands

| Command | Description |
|---------|-------------|
| `state get <key> [--scope session\|persistent\|project]` | Retrieve stored value |
| `state set <key> <value> [--scope] [--persist]` | Store a value |
| `state list [--scope]` | List all keys |
| `state clear [--scope] [--all]` | Clear state |

### State Scopes

| Scope | Storage Location | Use Case |
|-------|------------------|----------|
| `session` | Memory only | Temporary data |
| `persistent` | `~/.agent-arsenal/state.json` | Cross-session data |
| `project` | `./.arsenal-state` in project dir | Project-specific data |

## Usage

Once installed, you can run the CLI from anywhere:

```bash
# Show help
arsenal --help

# Show version
arsenal --version
```

## Configuration

### Config Command

Manage external command directories:

```bash
# Add an external command directory
arsenal config external-dir add /path/to/commands

# Remove an external command directory
arsenal config external-dir remove /path/to/commands

# List all configured directories
arsenal config external-dir list
```

### Sandbox Configuration

Manage sandbox security settings for executing Python/hybrid commands:

```bash
# View sandbox configuration
arsenal config sandbox show

# Set timeout for sandboxed command execution (seconds)
arsenal config sandbox set-timeout 30

# Set permission flags
arsenal config sandbox set-permissions --allow-read /tmp,/home --allow-env PATH,HOME

# Enable sandbox mode
arsenal config sandbox enable

# Disable sandbox mode (default)
arsenal config sandbox disable
```

### User Commands Directory

Personal commands can be added in `~/.arsenal/commands/`. This directory is automatically scanned—no configuration needed.

```
~/.arsenal/commands/
├── my-custom-group/
│   ├── info.md          # Group description
│   └── my-command.md   # Command file
└── another-command.md   # Root-level command
```

Built-in commands take precedence over user commands with the same name.

## Common Commands

### UUID / GUID

Generate UUIDs (version 4 or 7):

```bash
# Generate UUID v4 (random)
arsenal common uuid
# Output: 702a44c4-e649-481f-894a-0317f222f4a5

# Alias for uuid
arsenal common guid
```

### Hash

Compute cryptographic hashes:

```bash
# SHA256 hash (default)
arsenal common hash --input "mysecret"
# Output: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08

# MD5 hash
arsenal common hash --input "mysecret" --algorithm md5

# SHA512 hash
arsenal common hash --input "mysecret" --algorithm sha512
```

### Base64

Encode or decode Base64:

```bash
# Encode to Base64
arsenal common base64 --input "hello world"
# Output: aGVsbG8gd29ybGQ=

# Decode from Base64
arsenal common base64 --input "aGVsbG8gd29ybGQ=" --mode decode
```

### Code Utilities

#### JSON

Format, validate, or minify JSON:

```bash
# Format JSON
arsenal common code json --input '{"key":"value"}'
# Output:
# {
#   "key": "value"
# }

# Validate JSON (returns exit code)
arsenal common code json --input '{}' --mode validate

# Minify JSON
arsenal common code json --input '{"key": "value"}' --mode minify
```

#### URL

URL encode or decode strings:

```bash
# URL encode
arsenal common code url --input "hello world"
# Output: hello%20world

# URL decode
arsenal common code url --input "hello%20world" --mode decode
```

#### JWT

Decode JWT tokens (read-only):

```bash
# Decode JWT (shows header and payload)
arsenal common code jwt --token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Get specific part (header/payload)
arsenal common code jwt --token "..." --part payload
```

### Time Utilities

#### Timestamp / Now

Get current timestamp:

```bash
# Current datetime (default format)
arsenal common time now
# Output: 2026-02-26 23:56:41

# Get Unix timestamp
arsenal common time timestamp --format unix

# Custom format
arsenal common time now --format "%Y-%m-%d"

# Specific timezone
arsenal common time now --timezone UTC
arsenal common time now --timezone America/New_York
```

#### Timezone Convert

Convert time between timezones:

```bash
# Convert timestamp between timezones
arsenal common time convert --time "2024-01-01 12:00" --from-tz UTC --to-tz America/New_York
```

## State Management

Store and retrieve data across command invocations with different scopes:

```bash
# Set a value (default scope: session)
arsenal state set mykey "myvalue"

# Get a value
arsenal state get mykey

# List all keys
arsenal state list

# Clear state
arsenal state clear

# Use specific scope
arsenal state set project-key "value" --scope project
arsenal state get project-key --scope persistent

# Persist value across sessions
arsenal state set mykey "value" --persist
```

**Scopes:**
- `session` - Available during current terminal session (default)
- `persistent` - Persists across sessions (stored in `~/.agent-arsenal/state.json`)
- `project` - Project-specific state (stored in `.arsenal-state` in current directory)

### State Command Options

| Option | Description |
|--------|-------------|
| `--scope session\|persistent\|project` | Choose storage scope (default: session) |
| `--persist` | Persist value to disk (equivalent to `--scope persistent`) |
| `--all` | Clear all scopes (with `state clear`) |

## Watch Mode

Watch command files for changes and automatically reload:

```bash
# Watch with default settings (500ms debounce)
arsenal watch

# Custom debounce time in milliseconds
arsenal watch --debounce 1000
arsenal watch -d 2000
```

This is useful during development when adding or modifying command files.

### Watch Options

| Option | Description |
|--------|-------------|
| `--debounce MS, -d MS` | Debounce delay in milliseconds (default: 500) |

## Sandbox Security

Agent Arsenal supports a sandboxed execution environment for running Python/hybrid commands securely. The sandbox is built on Deno and provides fine-grained permission control.

```bash
# Show current sandbox configuration
arsenal config sandbox show

# Set execution timeout (seconds)
arsenal config sandbox set-timeout 30

# Configure permissions (individual flags)
arsenal config sandbox set-permissions --allow-read --allow-env

# Enable sandbox mode
arsenal config sandbox enable

# Disable sandbox mode
arsenal config sandbox disable
```

### Sandbox Permissions

| Permission | Description |
|------------|-------------|
| `allow_read` | Allow reading files |
| `allow_write` | Allow writing files |
| `allow_net` | Allow network requests |
| `allow_env` | Allow access to environment variables |
| `allow_run` | Allow running subprocesses |

### Notes

- **Default: Disabled** - The sandbox is disabled by default for maximum compatibility
- **Auto-disable** - Sandbox automatically disables if Deno is not installed
- **Timeout** - Maximum execution time for sandboxed commands (default: 60 seconds)

## Development

### Project Structure

```
agent-arsenal/
├── src/
│   └── agent_arsenal/
│       ├── __init__.py       # Package initialization
│       ├── main.py           # CLI entry point
│       ├── config.py         # Configuration management
│       ├── state.py          # State management
│       ├── watcher.py        # File watching for hot reload
│       ├── registry.py       # Command discovery
│       ├── parser.py         # Command file parsing
│       ├── executor.py       # Command execution
│       ├── commands/         # Markdown-based commands
│       │   ├── common/       # Common utilities
│       │   │   ├── uuid.md
│       │   │   ├── hash.md
│       │   │   ├── base64.md
│       │   │   ├── code/     # Code utilities
│       │   │   │   ├── json.md
│       │   │   │   ├── url.md
│       │   │   │   └── jwt.md
│       │   │   └── time/     # Time utilities
│       │   │       ├── timestamp.md
│       │   │       └── convert.md
│       │   └── state/        # State commands
│       └── handlers/         # Python execution handlers
├── pyproject.toml            # Project configuration
├── README.md                 # This file
└── .gitignore               # Git ignore patterns
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
- **jinja2** - Template rendering (optional, for template commands)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for full text.
