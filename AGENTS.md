# AGENT.md

## Quick Start

- **Package**: `agent-arsenal` — Global CLI for coding agents (hierarchical, markdown-based commands)
- **CLI entrypoint**: `arsenal` (install via `uv tool install . [--editable]`)
- **Dependency manager**: `uv` with `pyproject.toml` (build: uv_build)
- **Install (dev)**: `uv tool install . --editable` or run locally: `uv run arsenal --help`
- **Run tests**: `uv run pytest` (or `make test` if Makefile added)
- **Lint**: Run `ruff`, `mypy` (or `make lint` when available) before committing

## Package Structure

- **Source**: `src/agent_arsenal/` (installable package)
  - `main.py` — CLI entry point (Typer)
  - `registry.py` — Command discovery and loading from filesystem
  - `parser.py` — Frontmatter parsing from markdown command files
  - `executor.py` — Execution dispatch (prompt / python / hybrid / template)
  - `commands/` — Markdown-based command definitions (hierarchical folders)
  - `handlers/` — Python execution functions (for `python` / `hybrid` execution types)
- **Commands**: `src/agent_arsenal/commands/` — folder-based groups (e.g. `database/`, `api/`, `project/`, `django/`), each with `info.md` (group help) and `<name>.md` (leaf commands)
- **Tests**: `tests/` (pytest) when added; keep tests isolated and independent

## Key Conventions

### Public API

- Export public functions/classes from `src/agent_arsenal/__init__.py`
- Keep implementation details in modules; avoid leaking internals in the public API

### Commands and Execution

- Commands live in `commands/` as `.md` files with YAML frontmatter (name, description, args, execution_type, etc.)
- `info.md` in a folder provides group-level help; other `.md` files are leaf commands
- Execution types: `prompt` (Phase 1), `python` / `hybrid` (Phase 2), `template` (Phase 3)
- Add new commands by adding a new `.md` file; no server restart or registration required
- Python handlers for `python`/`hybrid` live under `handlers/` and are referenced in frontmatter (`python_function`)

### Optional / Phased Features

- **Hot reload**: `--watch` and `ARSENAL_WATCH` (Phase 3); use `watchfiles` for filesystem monitoring
- **State**: Session and persistent state (e.g. `~/.agent-arsenal/state.json`) as per PRD

### Testing & Code Quality

- **TDD**: Prefer writing failing tests first, then minimal code to pass (Red → Green → Refactor)
- Use **pytest** and fixtures in `tests/conftest.py` when tests exist; keep tests isolated and independent
- **Type hints**: Use for function signatures, methods, and class attributes
- **Linting**: Run ruff/mypy (or `make lint`) before committing
- Mark slow/integration tests with pytest markers (`@pytest.mark.slow`, `@pytest.mark.integration`)

## Git Rules

- Use **conventional commits** (type: description)
- Add detailed bulleted descriptions to the commits, highlighting the changes in the commit
- **Commit types**:
  - `feat`: Major user-facing features or substantial new capabilities
  - `chore`: Incremental improvements, internal changes, config, deps, tooling
  - `fix`: Bug fixes and corrections
  - `refactor`: Code restructuring without behavior changes
  - `docs`: Documentation updates
  - `test`: Adding or updating tests
  - `perf`: Performance improvements
- **Examples**:
  - ✅ `feat: add YAML formatter for Pydantic models`
  - ✅ `chore: add ruff rule for import sorting`
  - ✅ `fix: handle optional fields in jsonish formatter`
  - ❌ `feat: update pyproject` (use `chore`)

## Project-Specific Rules

### Do's

- Follow existing patterns for similar code (registry, parser, executor, commands, handlers)
- Run lint before committing
- Use type hints; keep the package typed
- Prefer SOLID principles; keep registry, parser, executor and command definitions clearly separated
- Add tests for new behavior; mock filesystem or optional deps when appropriate
- Keep command help and context usage minimal (target &lt;500 tokens per invocation per PRD)
- Always use dict, list for types instead of Typing Dict, List and always use | instead of typing Optional

### Don'ts

- Change public API in `__init__.py` without considering backward compatibility
- Put heavy or optional dependencies in core install (use extras if needed: `dev`, etc.)
- Skip tests or lint for new code
- Commit secrets or credentials
- Execute arbitrary code from `.md` file content (sandbox/handlers only)

## Boundaries

- **Allowed**: Read files, run tests, format/lint, change `src/agent_arsenal` and `tests`, update docs and command markdown under `commands/`
- **Ask first**: Add or bump dependencies, change build/publish config, alter supported Python versions
- **Never**: Commit secrets, disable security or lint checks, break documented public API without a plan

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->
