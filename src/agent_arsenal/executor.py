"""Command execution dispatcher."""

from __future__ import annotations

import os
import subprocess
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
    BASH = "bash"
    TEMPLATE = "template"


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

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
        from agent_arsenal.parser import parse_markdown_command, get_handler_info

        fm, _ = parse_markdown_command(command_obj.path)
        
        # Use get_handler_info to determine execution type
        handler_info = get_handler_info(fm)
        exec_type = handler_info.get("type", "prompt")

        if exec_type == "prompt":
            return self.execute_prompt(command_obj.path, args)
        elif exec_type == "python":
            return self.execute_python(command_obj, args)
        elif exec_type == "bash":
            return self.execute_bash(command_obj, args)
        elif exec_type == "template":
            return self.execute_template(command_obj.path, args)
        elif exec_type == "node":
            return self.execute_node(command_obj, args)

        return CommandResult(
            success=False,
            output="",
            error=f"Unknown execution type: {exec_type}",
        )

    def _find_handler_module(self, command_obj: "Command", handler_path: str):
        """Find handler module from executable_path.
        
        Supports:
        - Full path: "timestamp.handle_timestamp" -> handlers.timestamp.handle_timestamp
        - Co-located: looks for handlers/<group>/handlers/<name>.py first
        
        Args:
            command_obj: Command object
            handler_path: Path to handler (module.function format)
            
        Returns:
            Tuple of (module, function_name)
        """
        from importlib import import_module
        
        # Determine the base path for handler lookup
        command_dir = command_obj.path.parent
        command_name = command_obj.name
        parent_name = command_obj.parent or ""
        
        # Try co-located handler first (per spec)
        # Format: commands/<group>/handlers/<command_name>.py
        if "." in handler_path:
            handler_module_name, handler_func_name = handler_path.rsplit(".", 1)
        else:
            handler_module_name = handler_path
            handler_func_name = f"handle_{command_name}"
        
        # Check for co-located handler
        co_located_handler_dir = command_dir / "handlers"
        if co_located_handler_dir.exists():
            co_located_path = co_located_handler_dir / f"{handler_module_name}.py"
            if co_located_path.exists():
                try:
                    # Import from commands.<group>.handlers.<module>
                    if parent_name:
                        module_path = f"agent_arsenal.commands.{parent_name}.handlers.{handler_module_name}"
                    else:
                        module_path = f"agent_arsenal.handlers.{handler_module_name}"
                    handler_module = import_module(module_path)
                    handler_func = getattr(handler_module, handler_func_name)
                    return handler_module, handler_func
                except (ImportError, AttributeError):
                    pass  # Fall through to group-level handler
        
        # Fall back to group-level handler (handlers/<module>.py)
        try:
            handler_module = import_module(f"agent_arsenal.handlers.{handler_module_name}")
            handler_func = getattr(handler_module, handler_func_name)
            return handler_module, handler_func
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Handler not found: {handler_path} (tried co-located and group-level)") from e

    def execute_python(self, command_obj: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute Python function command.

        Args:
            command_obj: Command object
            args: Command arguments

        Returns:
            CommandResult with function output
        """
        from agent_arsenal.parser import parse_markdown_command, get_handler_info

        try:
            frontmatter, _ = parse_markdown_command(command_obj.path)
            handler_info = get_handler_info(frontmatter)
            
            handler_path = handler_info.get("path", "")
            if not handler_path:
                return CommandResult(
                    success=False,
                    output="",
                    error="executable_path not specified in frontmatter",
                )

            # Find and import the handler
            _, handler_func = self._find_handler_module(command_obj, handler_path)

            # Call the handler with args
            result = handler_func(**args)

            return CommandResult(success=True, output=str(result))
        except ImportError as e:
            return CommandResult(
                success=False, output="", error=f"Handler not found: {e}"
            )
        except Exception as e:
            return CommandResult(
                success=False, output="", error=str(e)
            )

    def execute_bash(self, command_obj: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute bash script command.

        Args:
            command_obj: Command object
            args: Command arguments (passed as environment variables)

        Returns:
            CommandResult with script output
        """
        from agent_arsenal.parser import parse_markdown_command, get_handler_info

        try:
            frontmatter, _ = parse_markdown_command(command_obj.path)
            handler_info = get_handler_info(frontmatter)
            
            script_path = handler_info.get("path", "")
            inline_script = handler_info.get("inline", "")
            
            # Prepare environment variables from args
            # Start with system environment to ensure PATH is available
            env = os.environ.copy()
            for key, value in args.items():
                # Convert key to uppercase for environment variable names
                env_key = key.upper()
                # Convert value to string
                env[env_key] = str(value)
            
            if inline_script:
                # Execute inline script
                result = subprocess.run(
                    ["bash", "-c", inline_script],
                    capture_output=True,
                    text=True,
                    env=env,
                )
            elif script_path:
                # Execute external script
                # Resolve script path relative to command file
                script_dir = command_obj.path.parent
                full_script_path = script_dir / script_path
                
                if not full_script_path.exists():
                    # Try from handlers directory
                    full_script_path = script_dir / "handlers" / script_path
                
                if not full_script_path.exists():
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"Script not found: {script_path}",
                    )
                
                result = subprocess.run(
                    ["bash", str(full_script_path)],
                    capture_output=True,
                    text=True,
                    env=env,
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error="No bash script specified (need executable_path or executable_inline)",
                )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}" if output else result.stderr
            
            if result.returncode != 0:
                return CommandResult(
                    success=False,
                    output=output,
                    error=f"Script exited with code {result.returncode}",
                )
            
            return CommandResult(success=True, output=output.strip())
            
        except Exception as e:
            return CommandResult(
                success=False, output="", error=str(e)
            )

    def execute_node(self, command_obj: "Command", args: Dict[str, Any]) -> CommandResult:
        """Execute Node.js script command.

        Args:
            command_obj: Command object
            args: Command arguments (passed as environment variables)

        Returns:
            CommandResult with script output
        """
        from agent_arsenal.parser import parse_markdown_command, get_handler_info

        try:
            frontmatter, _ = parse_markdown_command(command_obj.path)
            handler_info = get_handler_info(frontmatter)
            
            script_path = handler_info.get("path", "")
            inline_script = handler_info.get("inline", "")
            
            import subprocess

            # Check for Node.js availability first
            node_check = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
            )
            if node_check.returncode != 0:
                return CommandResult(
                    success=False,
                    output="",
                    error="Node.js is not installed or not in PATH",
                )
            
            # Prepare environment variables from args
            # Start with system environment to ensure PATH is available
            env = os.environ.copy()
            for key, value in args.items():
                env_key = key.upper()
                env[env_key] = str(value)
            
            if inline_script:
                # Execute inline script
                result = subprocess.run(
                    ["node", "-e", inline_script],
                    capture_output=True,
                    text=True,
                    env=env,
                )
            elif script_path:
                # Execute external script
                script_dir = command_obj.path.parent
                full_script_path = script_dir / script_path
                
                if not full_script_path.exists():
                    # Try from handlers directory
                    full_script_path = script_dir / "handlers" / script_path
                
                if not full_script_path.exists():
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"Script not found: {script_path}",
                    )
                
                result = subprocess.run(
                    ["node", str(full_script_path)],
                    capture_output=True,
                    text=True,
                    env=env,
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error="No Node.js script specified (need executable_path or executable_inline)",
                )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}" if output else result.stderr
            
            if result.returncode != 0:
                return CommandResult(
                    success=False,
                    output=output,
                    error=f"Script exited with code {result.returncode}",
                )
            
            return CommandResult(success=True, output=output.strip())
            
        except Exception as e:
            return CommandResult(
                success=False, output="", error=str(e)
            )

    def execute_template(
        self, command_path: Path, args: Dict[str, Any]
    ) -> CommandResult:
        """Execute template command (Jinja2 rendering).

        Args:
            command_path: Path to the command .md file
            args: Command arguments

        Returns:
            CommandResult with rendered template
        """
        import os

        try:
            from agent_arsenal.parser import parse_markdown_command

            # Parse the markdown file
            frontmatter, body = parse_markdown_command(command_path)

            # Build context from args + environment variables
            context = {}

            # Add command args to context
            context.update(args)

            # Add environment variables to context (uppercase keys)
            for key, value in os.environ.items():
                context[key.upper()] = value

            # Add some useful built-in variables
            context["COMMAND_PATH"] = str(command_path)
            context["COMMAND_NAME"] = command_path.stem

            # Render the template
            from jinja2 import BaseLoader, Environment, TemplateSyntaxError, StrictUndefined

            env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
            template = env.from_string(body)

            rendered = template.render(**context)

            return CommandResult(success=True, output=rendered)

        except TemplateSyntaxError as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Template syntax error: {e}",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Template execution error: {e}",
            )


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