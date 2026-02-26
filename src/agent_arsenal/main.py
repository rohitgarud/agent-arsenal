"""Main CLI entry point for Agent Arsenal."""

from __future__ import annotations

from pathlib import Path

import click
import typer
from rich.console import Console
from typing import Any, Dict, List

from agent_arsenal import __version__
from agent_arsenal.config import get_command_directories
from agent_arsenal.executor import CommandExecutor
from agent_arsenal.registry import Command, CommandGroup, CommandRegistry

# Get commands directory
COMMANDS_DIR = Path(__file__).parent / "commands"
external_dirs = get_command_directories()
registry = CommandRegistry(COMMANDS_DIR, external_dirs)

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
        console.print(
            "[yellow]No external command directories registered.[/yellow]"
        )
        return

    console.print("[bold]Registered command directories:[/bold]")
    for d in dirs:
        exists = "✓" if d.exists() else "✗"
        status = (
            f"[green]{exists}[/green]"
            if d.exists()
            else f"[red]{exists}[/red]"
        )
        console.print(f"  {status} {d}")


# State commands
@app.command("state-get")
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


@app.command("state-set")
def state_set(
    key: str = typer.Argument(..., help="State key to set"),
    value: str = typer.Argument(..., help="Value to store"),
    scope: str = typer.Option(
        "session", "--scope", "-s", help="Scope: session, persistent, project"
    ),
    persist: bool = typer.Option(
        False, "--persist", help="Persist to disk immediately (for persistent scope)"
    ),
):
    """Set a value in state."""
    from agent_arsenal.state import state

    scope_enum = _parse_scope(scope)
    state.set(key, value, scope_enum)

    if persist and scope == "persistent":
        state.persist()

    console.print(f"[green]Set {key} = {value} in {scope} scope[/green]")


@app.command("state-list")
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


@app.command("state-clear")
def state_clear(
    scope: str = typer.Option(
        "session", "--scope", "-s", help="Scope: session, persistent, project (default: all)"
    ),
    all_scopes: bool = typer.Option(
        False, "--all", "-a", help="Clear all scopes"
    ),
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
_command_info: Dict[str, Any] = {}


def generate_command_function(cmd: Command, args_def: List[Dict[str, Any]]):
    """Generate a command function using exec with proper parameter definitions.

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

    # Build function source code
    if not args_def:
        # No arguments
        func_code = f'''
def {cmd.name}():
    """{description}"""
    executor = CommandExecutor()
    result = executor.execute(cmd, {{}})
    if result.success:
        console.print(result.output)
    else:
        console.print(f"[bold red]Error:[/bold red] {{result.error}}")
'''
    else:
        # Build parameter list and option decorators
        params = []
        decorators = []
        
        for i, arg in enumerate(args_def):
            arg_name = arg.get("name", "")
            arg_type = arg.get("type", "string")
            arg_default = arg.get("default")
            arg_description = arg.get("description", "")
            
            param_name = arg_name.replace("-", "_")
            opt_name = f"--{arg_name}"
            
            # Determine type
            if arg_type == "boolean":
                param_type = "bool"
                default_val = "True" if arg_default else "False"
            elif arg_type == "integer":
                param_type = "int"
                default_val = repr(arg_default) if arg_default is not None else "None"
            else:
                param_type = "str"
                default_val = repr(arg_default) if arg_default is not None else '""'
            
            params.append(f"{param_name}: {param_type} = None")
            
            # Build Click option
            if arg_type == "boolean":
                decorators.append(
                    f'@click.option("{opt_name}", is_flag=True, default={default_val}, help="{arg_description}", show_default=True)'
                )
            elif arg_type == "integer":
                decorators.append(
                    f'@click.option("{opt_name}", type=int, default={default_val}, help="{arg_description}", show_default=True)'
                )
            else:
                decorators.append(
                    f'@click.option("{opt_name}", default={default_val}, help="{arg_description}", show_default=True)'
                )
        
        params_str = ", ".join(params)
        decorators_str = "\n".join(reversed(decorators))
        
        # Build function body - build args dict manually
        args_lines = []
        for arg in args_def:
            param_name = arg.get("name", "").replace("-", "_")
            args_lines.append(f'    if {param_name} is not None:')
            args_lines.append(f'        args["{param_name}"] = {param_name}')
        
        args_body = "\n".join(args_lines) if args_lines else "    pass"
        
        func_code = f'''
{decorators_str}
def {cmd.name}({params_str}):
    """{description}"""
    args = dict()
{args_body}
    
    executor = CommandExecutor()
    result = executor.execute(cmd, args)
    if result.success:
        console.print(result.output)
    else:
        console.print(f"[bold red]Error:[/bold red] {{result.error}}")
'''

    # Execute the code to create the function
    namespace = {
        "click": click,
        "CommandExecutor": CommandExecutor,
        "console": console,
        "cmd": cmd,
    }
    exec(func_code, namespace)
    
    return namespace[cmd.name]


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
root_group = registry.scan_all()
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
        commands_dir=COMMANDS_DIR,
        reload_callback=lambda: registry.scan_all(),
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