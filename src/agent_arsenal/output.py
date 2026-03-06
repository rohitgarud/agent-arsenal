"""Output management for CLI operations.

This module provides the OutputManager class which controls all CLI output behavior,
including quiet mode, verbose mode, and color control.
"""

import json
from dataclasses import dataclass
from sys import stderr, stdout
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.theme import Theme

if TYPE_CHECKING:
    from agent_arsenal.executor import CommandResult


@dataclass
class OutputConfig:
    """Configuration for output behavior.

    Attributes:
        quiet: If True, suppress all non-essential output (colors, verbose info).
        verbose: If True, show additional debug information.
        no_color: If True, disable color output regardless of other settings.
        json: If True, output machine-readable JSON instead of human-friendly text.
        debug: If True, enable debug mode for additional diagnostics.
    """

    quiet: bool = False
    verbose: bool = False
    no_color: bool = False
    json: bool = False
    debug: bool = False


class OutputManager:
    """Manages all CLI output operations.

    This class centralizes output handling, allowing consistent control over
    what gets printed to stdout/stderr based on configuration (quiet mode, etc.).
    """

    def __init__(self, config: OutputConfig) -> None:
        """Initialize the OutputManager with the given configuration.

        Args:
            config: OutputConfig object defining output behavior.
        """
        self._config = config
        self._console_stdout, self._console_stderr = self._setup_consoles()

    def _setup_consoles(self) -> tuple[Console, Console]:
        """Set up Rich Console instances based on configuration.

        Returns:
            Tuple of (stdout_console, stderr_console).
        """
        # Determine if we should use no color
        use_no_color = self._config.no_color or self._config.quiet

        # Create theme for custom styles (only if not in no-color mode)
        theme = None
        if not use_no_color:
            theme = Theme(
                {
                    "result": "green",
                    "error": "bold red",
                    "info": "cyan",
                    "warning": "yellow",
                    "verbose": "dim",
                }
            )

        # stdout console - use color unless disabled
        # Don't force_terminal to allow proper test capture
        console_stdout = Console(
            file=stdout,
            force_terminal=False,
            no_color=use_no_color,
            theme=theme,
        )

        # stderr console - same settings
        console_stderr = Console(
            file=stderr,
            force_terminal=False,
            no_color=use_no_color,
            theme=theme,
        )

        return console_stdout, console_stderr

    def _is_non_interactive(self) -> bool:
        """Check if output is being piped or redirected.

        Returns:
            True if stdout is not a TTY.
        """
        return not self._console_stdout.is_terminal

    @property
    def config(self) -> OutputConfig:
        """Get the current output configuration.

        Returns:
            The OutputConfig instance.
        """
        return self._config

    @property
    def is_quiet(self) -> bool:
        """Check if quiet mode is enabled.

        Returns:
            True if quiet mode is enabled.
        """
        return self._config.quiet

    @property
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled.

        Returns:
            True if verbose mode is enabled.
        """
        return self._config.verbose

    def _print_json(self, result: "CommandResult") -> None:
        """Print command result in JSON format.

        Args:
            result: The CommandResult to print as JSON.
        """
        output_data = {
            "success": result.success,
            "output": result.output,
            "error": result.error,
        }
        if result.metadata:
            output_data["metadata"] = result.metadata
        typer.echo(json.dumps(output_data))

    def _print_text(self, result: "CommandResult") -> None:
        """Print command result in human-friendly text format.

        Args:
            result: The CommandResult to print as text.
        """
        if self._config.quiet:
            # Plain text output in quiet mode - use built-in print
            print(result.output, file=stdout)
        else:
            # Rich-formatted output in normal mode
            self._console_stdout.print(result.output)

    def print_result(self, result: "CommandResult") -> None:
        """Print command result to stdout.

        This is the primary output method for command results.
        Routes to JSON or text output based on configuration.

        Args:
            result: The CommandResult containing the command execution result.
        """
        if self._config.json:
            self._print_json(result)
        else:
            self._print_text(result)

    def print_error(self, content: str) -> None:
        """Print error to stderr.

        Errors are always printed, but styled differently in quiet mode or JSON mode.

        Args:
            content: The error content to print.
        """
        if self._config.json:
            # JSON output for error case
            error_data = {"success": False, "output": "", "error": content}
            typer.echo(json.dumps(error_data))
        elif self._config.quiet:
            # Plain error in quiet mode - use built-in print
            print(content, file=stderr)
        else:
            # Rich-formatted error
            self._console_stderr.print(f"[error]Error:[/error] {content}")

    def print_verbose(self, content: str) -> None:
        """Print verbose debug information.

        This is suppressed in quiet mode.

        Args:
            content: The verbose content to print.
        """
        # In quiet mode, suppress verbose output entirely
        if self._config.quiet:
            return

        # In verbose mode, show the content
        if self._config.verbose:
            self._console_stderr.print(f"[verbose]{content}[/verbose]")

    def print_banner(self, content: str) -> None:
        """Print banner or header content.

        This is suppressed in quiet mode.

        Args:
            content: The banner content to print.
        """
        # Suppress banner in quiet mode
        if self._config.quiet:
            return

        self._console_stdout.print(content)

    def print_info(self, content: str) -> None:
        """Print informational message.

        This is suppressed in quiet mode.

        Args:
            content: The info content to print.
        """
        # Suppress info in quiet mode
        if self._config.quiet:
            return

        if self._config.no_color:
            # Plain text when no_color is set
            print(content, file=stdout)
        else:
            self._console_stdout.print(f"[info]{content}[/info]")


# Module-level default OutputManager for simple use cases
_default_config = OutputConfig()
_default_manager: OutputManager | None = None


def get_output_manager(config: OutputConfig | None = None) -> OutputManager:
    """Get a shared OutputManager instance.

    If no config is provided, returns a default manager.

    Args:
        config: Optional OutputConfig. If None, returns default manager.

    Returns:
        An OutputManager instance.
    """
    global _default_manager

    if config is None:
        if _default_manager is None:
            _default_manager = OutputManager(_default_config)
        return _default_manager

    return OutputManager(config)
