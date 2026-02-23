"""Main CLI entry point for Agent Arsenal."""

from pathlib import Path

import typer
from rich.console import Console

from agent_arsenal import __version__
from agent_arsenal.executor import CommandExecutor
from agent_arsenal.registry import Command, CommandGroup, CommandRegistry

# Get commands directory
COMMANDS_DIR = Path(__file__).parent / "commands"
registry = CommandRegistry(COMMANDS_DIR)

app = typer.Typer(
    name="arsenal",
    help="Agent Arsenal - A global CLI tool for coding agents to use in development",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


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

        def create_cmd_func(command_obj: Command):
            def cmd_func():
                executor = CommandExecutor()
                result = executor.execute(command_obj, {})

                if result.success:
                    console.print(result.output)
                else:
                    console.print(f"[bold red]Error:[/bold red] {result.error}")

            return cmd_func

        # Register the command name.
        # Dynamic argument generation will be added in Phase 2
        typer_app.command(name=cmd.name, help=f"Execute {cmd.name} command")(
            create_cmd_func(cmd)
        )


# Initialize registry and build CLI tree
root_group = registry.scan_directory()
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
