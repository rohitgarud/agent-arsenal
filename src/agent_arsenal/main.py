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