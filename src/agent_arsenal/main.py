"""Main CLI entry point for Agent Arsenal."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from agent_arsenal import __version__
from agent_arsenal.config import (
    get_command_directories,
    load_sandbox_config,
    save_sandbox_config,
)
from agent_arsenal.executor import CommandExecutor
from agent_arsenal.registry import Command, CommandGroup, CommandRegistry

# Lazy initialization for registry
_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    """Lazily initialize the command registry.

    This avoids importing the registry at module load time,
    which improves startup performance and allows for better testing.

    Returns:
        The initialized CommandRegistry instance
    """
    global _registry
    if _registry is None:
        commands_dir = Path(__file__).parent / "commands"
        external_dirs = get_command_directories()
        _registry = CommandRegistry(commands_dir, external_dirs)
    return _registry


def get_commands_dir() -> Path:
    """Get the commands directory path."""
    return Path(__file__).parent / "commands"


app = typer.Typer(
    name="arsenal",
    help="Agent Arsenal - A global CLI tool for coding agents to use in development",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()

# Config command group
config_app = typer.Typer(
    name="config",
    help="Manage configuration settings",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

# State command group
state_app = typer.Typer(
    name="state",
    help="Manage state (session, persistent, project scopes)",
    no_args_is_help=True,
)
app.add_typer(state_app, name="state")

# External directories subcommand group under config
external_dir_app = typer.Typer(
    name="external-dir",
    help="Manage external command directories",
    no_args_is_help=True,
)
config_app.add_typer(external_dir_app, name="external-dir")


@external_dir_app.command("add")
def external_dir_add(path: str):
    """Add an external command directory.

    Args:
        path: Path to the external command directory
    """
    from agent_arsenal.config import add_command_directory

    path_obj = Path(path).expanduser().resolve()
    result = add_command_directory(path_obj)

    if result:
        console.print(f"[green]Added:[/green] {path_obj}")
    else:
        console.print(f"[yellow]Already registered:[/yellow] {path_obj}")


@external_dir_app.command("remove")
def external_dir_remove(path: str):
    """Remove an external command directory.

    Args:
        path: Path to the external command directory to remove
    """
    from agent_arsenal.config import remove_command_directory

    path_obj = Path(path).expanduser().resolve()
    result = remove_command_directory(path_obj)

    if result:
        console.print(f"[green]Removed:[/green] {path_obj}")
    else:
        console.print(f"[yellow]Not found:[/yellow] {path_obj}")


@external_dir_app.command("list")
def external_dir_list():
    """List all registered external command directories."""
    from agent_arsenal.config import list_command_directories

    dirs = list_command_directories()

    if not dirs:
        console.print("[yellow]No external command directories registered.[/yellow]")
        return

    console.print("[bold]Registered command directories:[/bold]")
    for d in dirs:
        exists = "✓" if d.exists() else "✗"
        status = f"[green]{exists}[/green]" if d.exists() else f"[red]{exists}[/red]"
        console.print(f"  {status} {d}")


# Sandbox subcommand group under config
sandbox_app = typer.Typer(
    name="sandbox",
    help="Manage sandbox configuration",
    no_args_is_help=True,
)
config_app.add_typer(sandbox_app, name="sandbox")


@sandbox_app.command("show")
def sandbox_show():
    """Display current sandbox configuration."""
    config = load_sandbox_config()
    console.print("[bold]Sandbox Configuration:[/bold]")
    console.print(f"  Enabled: {config.enabled}")
    console.print(f"  Timeout: {config.timeout_seconds}s")
    console.print("  Default Permissions:")
    perms = config.default_permissions
    console.print(f"    allow_read: {perms.allow_read or '[]'}")
    console.print(f"    allow_write: {perms.allow_write or '[]'}")
    console.print(f"    allow_net: {perms.allow_net}")
    console.print(f"    allow_env: {perms.allow_env or '[]'}")
    console.print(f"    allow_run: {perms.allow_run}")


@sandbox_app.command("set-timeout")
def sandbox_set_timeout(seconds: int = typer.Argument(..., help="Timeout in seconds")):
    """Set sandbox timeout in seconds."""
    config = load_sandbox_config()
    config.timeout_seconds = seconds
    save_sandbox_config(config)
    console.print(f"[green]Sandbox timeout set to {seconds} seconds[/green]")


@sandbox_app.command("set-permissions")
def sandbox_set_permissions(
    allow_read: str | None = typer.Option(
        None, "--allow-read", help="Comma-separated list of allowed read paths"
    ),
    allow_write: str | None = typer.Option(
        None, "--allow-write", help="Comma-separated list of allowed write paths"
    ),
    allow_net: bool | None = typer.Option(
        None, "--allow-net", help="Allow network access"
    ),
    allow_env: str | None = typer.Option(
        None,
        "--allow-env",
        help="Comma-separated list of allowed environment variables",
    ),
    allow_run: bool | None = typer.Option(
        None, "--allow-run", help="Allow subprocess spawning"
    ),
):
    """Set sandbox default permissions."""
    config = load_sandbox_config()
    perms = config.default_permissions

    if allow_read is not None:
        perms.allow_read = [p.strip() for p in allow_read.split(",") if p.strip()]
    if allow_write is not None:
        perms.allow_write = [p.strip() for p in allow_write.split(",") if p.strip()]
    if allow_net is not None:
        perms.allow_net = allow_net
    if allow_env is not None:
        perms.allow_env = [e.strip() for e in allow_env.split(",") if e.strip()]
    if allow_run is not None:
        perms.allow_run = allow_run

    config.default_permissions = perms
    save_sandbox_config(config)
    console.print("[green]Sandbox permissions updated[/green]")


@sandbox_app.command("enable")
def sandbox_enable():
    """Enable sandbox (default)."""
    config = load_sandbox_config()
    config.enabled = True
    save_sandbox_config(config)
    console.print("[green]Sandbox enabled[/green]")


@sandbox_app.command("disable")
def sandbox_disable():
    """Disable sandbox globally."""
    config = load_sandbox_config()
    config.enabled = False
    save_sandbox_config(config)
    console.print("[green]Sandbox disabled[/green]")


# State commands
@state_app.command("get")
def state_get(
    key: str = typer.Argument(..., help="State key to retrieve"),
    scope: str = typer.Option(
        "session", "--scope", "-s", help="Scope: session, persistent, project"
    ),
):
    """Get a value from state."""
    from agent_arsenal.state import state

    scope_enum = _parse_scope(scope)
    value = state.get(key, scope_enum)

    if value is None:
        console.print(f"[yellow]Key '{key}' not found in {scope} scope[/yellow]")
    else:
        console.print(f"[bold]{key}:[/bold] {value}")


@state_app.command("set")
def state_set(
    key: str = typer.Argument(..., help="State key to set"),
    value: str = typer.Argument(..., help="Value to store"),
    scope: str = typer.Option(
        "session", "--scope", "-s", help="Scope: session, persistent, project"
    ),
    persist: bool = typer.Option(
        False,
        "--persist",
        help="Persist to disk immediately (for persistent scope)",
    ),
):
    """Set a value in state."""
    from agent_arsenal.state import state

    scope_enum = _parse_scope(scope)
    state.set(key, value, scope_enum)

    if persist and scope == "persistent":
        state.persist()

    console.print(f"[green]Set {key} = {value} in {scope} scope[/green]")


@state_app.command("list")
def state_list(
    scope: str = typer.Option(
        "session", "--scope", "-s", help="Scope: session, persistent, project"
    ),
):
    """List all keys in state."""
    from agent_arsenal.state import state

    scope_enum = _parse_scope(scope)
    keys = state.list_keys(scope_enum)

    if not keys:
        console.print(f"[yellow]No keys in {scope} scope[/yellow]")
        return

    console.print(f"[bold]Keys in {scope} scope:[/bold]")
    for key in keys:
        value = state.get(key, scope_enum)
        console.print(f"  {key}: {value}")


@state_app.command("clear")
def state_clear(
    scope: str = typer.Option(
        "session",
        "--scope",
        "-s",
        help="Scope: session, persistent, project (default: all)",
    ),
    all_scopes: bool = typer.Option(False, "--all", "-a", help="Clear all scopes"),
):
    """Clear state for a scope."""
    from agent_arsenal.state import state

    if all_scopes:
        state.clear()
        console.print("[green]Cleared all state scopes[/green]")
    else:
        scope_enum = _parse_scope(scope)
        state.clear(scope_enum)
        console.print(f"[green]Cleared {scope} scope[/green]")


def _parse_scope(scope_str: str):
    """Parse scope string to Scope enum.

    Args:
        scope_str: Scope string (session, persistent, project)

    Returns:
        Scope enum value

    Raises:
        typer.BadParameter: If scope is invalid
    """
    from agent_arsenal.state import Scope

    scope_str = scope_str.lower()
    if scope_str == "session":
        return Scope.SESSION
    elif scope_str == "persistent":
        return Scope.PERSISTENT
    elif scope_str == "project":
        return Scope.PROJECT
    else:
        raise typer.BadParameter(
            f"Invalid scope: {scope_str}. Must be session, persistent, or project"
        )


# Storage for command info
_command_info: dict[str, Any] = {}


def generate_command_function(cmd: Command, args_def: list[dict[str, Any]]):
    """Generate a command function with explicit Typer parameters.

    This replaces the previous exec()-based approach with explicit Typer
    command definitions, improving type safety and maintainability.

    Args:
        cmd: Command object
        args_def: List of argument definitions from frontmatter

    Returns:
        A command function with explicit parameters
    """
    from agent_arsenal.parser import parse_markdown_command

    frontmatter, _ = parse_markdown_command(cmd.path)
    description = frontmatter.get("description", f"Execute {cmd.name} command")

    # Store command info for conversion
    key = str(cmd.path)
    _command_info[key] = {
        arg.get("name", "").replace("-", "_"): {
            "type": arg.get("type", "string"),
            "default": arg.get("default"),
        }
        for arg in args_def
    }

    # Create a closure that captures the command and args_def
    def create_command_func(
        command: Command,
        args_definitions: list[dict[str, Any]],
    ):
        """Create a Typer command function with explicit type-annotated parameters."""

        def command_func(*func_args: Any, **func_kwargs: Any) -> None:
            """Execute the command with provided arguments."""
            # Build args dict from kwargs, filtering out None values
            args: dict[str, Any] = {}
            for key, value in func_kwargs.items():
                if value is not None:
                    args[key] = value

            # Execute the command
            executor = CommandExecutor()
            result = executor.execute(command, args)

            if result.success:
                console.print(result.output)
            else:
                console.print(f"[bold red]Error:[/bold red] {result.error}")

        # Set function metadata
        command_func.__name__ = command.name
        command_func.__doc__ = description

        return command_func

    # Build the command function with explicit parameters
    func = create_command_func(cmd, args_def)

    # Add type annotations and defaults based on args_def
    # We create a wrapper that properly handles the arguments
    if not args_def:
        # No arguments case - simple wrapper
        def no_args_func() -> None:
            """Execute the command with no arguments."""
            executor = CommandExecutor()
            result = executor.execute(cmd, {})
            if result.success:
                console.print(result.output)
            else:
                console.print(f"[bold red]Error:[/bold red] {result.error}")

        no_args_func.__name__ = cmd.name
        no_args_func.__doc__ = description
        return no_args_func
    else:
        # Create a dynamic function with explicit Typer parameters using functools.wraps
        import functools

        # Build the signature with proper annotations
        from inspect import Parameter, signature

        # Create parameters based on args_def
        params = []
        for arg in args_def:
            arg_name = arg.get("name", "")
            arg_type = arg.get("type", "string")
            arg_default = arg.get("default")

            param_name = arg_name.replace("-", "_")

            # Determine the default value and annotation
            if arg_type == "boolean":
                default = arg_default if arg_default is not None else False
                annotation: type = bool
            elif arg_type == "integer":
                default = arg_default if arg_default is not None else 0
                annotation = int
            elif arg_type == "float":
                default = arg_default if arg_default is not None else 0.0
                annotation = float
            else:
                default = arg_default if arg_default is not None else ""
                annotation = str

            # Create Parameter object
            param = Parameter(
                param_name,
                kind=Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
            params.append(param)

        # Create the signature
        sig = signature(func)
        sig = sig.replace(parameters=params)

        # Apply the signature to our function
        func.__signature__ = sig

        # Build a wrapper that handles the conversion properly
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            # Convert hyphenated keys to underscore keys
            normalized_kwargs: dict[str, Any] = {}
            for key, value in kwargs.items():
                if value is not None:
                    normalized_kwargs[key] = value

            # Build args dict
            args_dict: dict[str, Any] = {}
            for arg in args_def:
                arg_name = arg.get("name", "").replace("-", "_")
                if arg_name in normalized_kwargs:
                    args_dict[arg_name] = normalized_kwargs[arg_name]

            # Execute the command
            executor = CommandExecutor()
            result = executor.execute(cmd, args_dict)

            if result.success:
                console.print(result.output)
            else:
                console.print(f"[bold red]Error:[/bold red] {result.error}")

        wrapper.__name__ = cmd.name
        wrapper.__doc__ = description
        wrapper.__signature__ = sig  # type: ignore[attr-defined]

        return wrapper


def register_commands(typer_app: typer.Typer, group: CommandGroup):
    """Recursively register command groups and commands into Typer."""

    # Register subgroups
    for subgroup in group.subgroups:
        sub_app = typer.Typer(
            name=subgroup.name,
            help=subgroup.description or f"{subgroup.name} commands",
            no_args_is_help=True,
        )
        typer_app.add_typer(sub_app, name=subgroup.name)
        register_commands(sub_app, subgroup)

    # Register leaf commands
    for cmd in group.commands:
        from agent_arsenal.parser import parse_markdown_command

        frontmatter, _ = parse_markdown_command(cmd.path)
        args_def = frontmatter.get("args", [])

        # Generate command function
        cmd_func = generate_command_function(cmd, args_def)

        # Register with Typer
        typer_app.command(
            name=cmd.name,
            help=frontmatter.get("description", ""),
        )(cmd_func)

        # Register aliases if present
        aliases = frontmatter.get("aliases", [])
        for alias in aliases:
            typer_app.command(
                name=alias,
                help=frontmatter.get("description", ""),
            )(cmd_func)


# Initialize registry and build CLI tree
root_group = get_registry().scan_all()
register_commands(app, root_group)


# Watch command - reloads commands on file changes
@app.command("watch")
def watch(
    debounce: int = typer.Option(
        500,
        "--debounce",
        "-d",
        help="Debounce time in milliseconds",
    ),
):
    """Watch command files for changes and reload automatically."""
    from agent_arsenal.config import should_watch
    from agent_arsenal.watcher import CommandWatcher

    # Check if ARSENAL_WATCH env var is set
    if not should_watch():
        console.print(
            "[yellow]Warning: ARSENAL_WATCH not set. "
            "Use 'export ARSENAL_WATCH=1' to enable watch mode by default.[/yellow]"
        )

    console.print("[bold]Watching for changes in commands...[/bold]")
    console.print("Press Ctrl+C to stop.")

    # Create watcher
    watcher = CommandWatcher(
        commands_dir=get_commands_dir(),
        reload_callback=lambda: get_registry().scan_all(),
        debounce_ms=debounce,
    )

    # Run blocking watch
    try:
        watcher.watch()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print(f"Agent Arsenal version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode",
    ),
):
    """
    Agent Arsenal - A global CLI tool for coding agents to use in development.

    Commands are organized hierarchically based on the commands/ folder.
    Use --help with any group or command to see more details.
    """
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
    pass


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
