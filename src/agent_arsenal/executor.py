"""Command execution dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from agent_arsenal.registry import Command


class ExecutionType(Enum):
    """Types of command execution."""

    PROMPT = "prompt"
    PYTHON = "python"
    HYBRID = "hybrid"
    TEMPLATE = "template"


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CommandExecutor:
    """Dispatcher for executing commands based on execution type."""

    def __init__(self):
        """Initialize the executor."""
        pass

    def execute_prompt(self, command_path: Path, args: Dict[str, Any]) -> CommandResult:
        """Execute prompt-type command (return markdown instructions)."""
        from agent_arsenal.parser import parse_markdown_command

        try:
            frontmatter, body = parse_markdown_command(command_path)
            # Simple placeholder substitution for args
            output = body
            for key, value in args.items():
                output = output.replace(f"{{{key}}}", str(value))

            return CommandResult(success=True, output=output)
        except Exception as e:
            return CommandResult(success=False, output="", error=str(e))

    def execute(self, command_obj: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute a command based on its execution type."""
        from agent_arsenal.parser import parse_markdown_command

        fm, _ = parse_markdown_command(command_obj.path)
        exec_type = fm.get("execution_type", "prompt")

        if exec_type == "prompt":
            return self.execute_prompt(command_obj.path, args)
        # TODO: Implement other types
        return CommandResult(
            success=False,
            output="",
            error=f"Execution type {exec_type} not implemented",
        )

    def execute_python(self, command: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute Python function command.

        Args:
            command: Command object
            args: Command arguments

        Returns:
            CommandResult with function output
        """
        # TODO: Implement Python execution
        # - Import and call python_function
        # - Pass args and state
        # - Return result
        pass

    def execute_hybrid(self, command: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute hybrid command (Python + prompt).

        Args:
            command: Command object
            args: Command arguments

        Returns:
            CommandResult with combined output
        """
        # TODO: Implement hybrid execution
        # - Execute Python function first
        # - Use result to render instructions
        # - Combine outputs
        pass

    def execute_template(
        self, command: "Command", args: Dict[str, Any]
    ) -> CommandResult:
        """Execute template command (Jinja2 rendering).

        Args:
            command: Command object
            args: Command arguments

        Returns:
            CommandResult with rendered template
        """
        # TODO: Implement template execution (Phase 3)
        pass


def render_instructions(
    command: "Command", args: Dict[str, Any], context: Optional[Dict] = None
) -> str:
    """Render command instructions with argument substitution.

    Args:
        command: Command object
        args: Command arguments
        context: Optional additional context

    Returns:
        Rendered markdown instructions
    """
    # TODO: Implement instruction rendering
    # - Support variable substitution
    # - Format nicely with Rich
    pass
