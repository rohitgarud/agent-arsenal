"""Command execution dispatcher."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent_arsenal.registry import Command

# Sandbox imports
from agent_arsenal.sandbox import (
    DenoSandboxExecutor,
    SandboxConfig,
)
from agent_arsenal.config import (
    get_sandbox_permissions_for_command,
    load_sandbox_config,
)


@dataclass
class CommandResult:
    """Result of command execution."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CommandExecutor:
    """Dispatcher for executing commands based on execution type."""

    def __init__(self):
        """Initialize the executor."""
        pass

    def execute_prompt(self, command_path: Path, args: dict[str, Any]) -> CommandResult:
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

    def execute(self, command_obj: "Command", args: dict[str, Any]) -> CommandResult:
        """Execute a command based on its execution type."""
        from agent_arsenal.parser import (
            get_handler_info,
            parse_markdown_command,
        )

        fm, _ = parse_markdown_command(command_obj.path)

        # Use get_handler_info to determine execution type
        handler_info = get_handler_info(fm)
        exec_type = handler_info.get("type", "prompt")

        # Extract sandbox config from frontmatter
        sandbox_enabled = fm.get("sandbox", True)  # Default: true (sandbox enabled)

        if sandbox_enabled:
            # Route to sandbox executor
            try:
                sandbox_config = load_sandbox_config()
            except Exception:
                # Fall back to defaults if config fails
                sandbox_config = SandboxConfig()

            if not sandbox_config.enabled:
                # Sandbox disabled globally - execute directly
                return self._execute_direct(command_obj, args, exec_type, handler_info)

            permissions = get_sandbox_permissions_for_command(fm, sandbox_config)

            # Check Deno availability
            sandbox_exec = DenoSandboxExecutor(sandbox_config)
            if not sandbox_exec._check_deno_available():
                return CommandResult(
                    success=False,
                    output="",
                    error="Deno is not installed. Install via: curl -fsSL https://deno.land/x/install/install.sh | sh",
                )

            # Execute in sandbox and convert result to executor's CommandResult
            sandbox_result = sandbox_exec.execute(
                execution_type=exec_type,
                script=handler_info.get("path") or handler_info.get("inline", ""),
                permissions=permissions,
                timeout=sandbox_config.timeout_seconds,
            )
            return CommandResult(
                success=sandbox_result.success,
                output=sandbox_result.output,
                error=sandbox_result.error,
                metadata=sandbox_result.metadata,
            )
        else:
            # Execute directly (no sandbox)
            return self._execute_direct(command_obj, args, exec_type, handler_info)

    def _execute_direct(
        self,
        command_obj: "Command",
        args: dict[str, Any],
        exec_type: str,
        handler_info: dict[str, Any],
    ) -> CommandResult:
        """Execute command directly without sandbox.

        Args:
            command_obj: Command object
            args: Command arguments
            exec_type: Execution type (prompt, python, bash, template, node)
            handler_info: Parsed handler info from frontmatter

        Returns:
            CommandResult
        """
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
            handler_module = import_module(
                f"agent_arsenal.handlers.{handler_module_name}"
            )
            handler_func = getattr(handler_module, handler_func_name)
            return handler_module, handler_func
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Handler not found: {handler_path} (tried co-located and group-level)"
            ) from e

    def execute_python(
        self, command_obj: "Command", args: dict[str, Any]
    ) -> CommandResult:
        """Execute Python function command.

        Args:
            command_obj: Command object
            args: Command arguments

        Returns:
            CommandResult with function output
        """
        from agent_arsenal.parser import (
            get_handler_info,
            parse_markdown_command,
        )

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
            return CommandResult(success=False, output="", error=str(e))

    def _execute_subprocess(
        self,
        command: "Command",
        args: dict[str, Any],
        runtime: str,
        script_path: str | None = None,
        inline_script: str | None = None,
    ) -> CommandResult:
        """Common subprocess execution logic for bash, node, etc.

        Args:
            command: Command object
            args: Command arguments (passed as environment variables)
            runtime: Runtime to use (e.g., "bash", "node")
            script_path: Path to external script file
            inline_script: Inline script to execute

        Returns:
            CommandResult with script output
        """
        # Check runtime availability first
        check = subprocess.run(
            [runtime, "--version"],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            return CommandResult(
                success=False,
                output="",
                error=f"{runtime} is not installed or not in PATH",
            )

        # Prepare environment variables from args
        # Start with system environment to ensure PATH is available
        env = os.environ.copy()
        for key, value in args.items():
            # Convert key to uppercase for environment variable names
            env_key = key.upper()
            # Convert value to string
            env[env_key] = str(value)

        # Determine script source and command
        if inline_script:
            # Different runtimes use different flags for inline scripts
            if runtime == "bash":
                cmd = [runtime, "-c", inline_script]
            else:
                # node, python, etc. use -e flag
                cmd = [runtime, "-e", inline_script]
        elif script_path:
            # Resolve script path relative to command file
            script_dir = command.path.parent
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

            cmd = [runtime, str(full_script_path)]
        else:
            return CommandResult(
                success=False,
                output="",
                error=f"No {runtime if runtime != 'node' else 'node.js'} script specified (need executable_path or executable_inline)",
            )

        # Execute the script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
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

    def execute_bash(
        self, command_obj: "Command", args: dict[str, Any]
    ) -> CommandResult:
        """Execute bash script command.

        Args:
            command_obj: Command object
            args: Command arguments (passed as environment variables)

        Returns:
            CommandResult with script output
        """
        from agent_arsenal.parser import (
            get_handler_info,
            parse_markdown_command,
        )

        try:
            frontmatter, _ = parse_markdown_command(command_obj.path)
            handler_info = get_handler_info(frontmatter)

            script_path = handler_info.get("path", "")
            inline_script = handler_info.get("inline", "")

            return self._execute_subprocess(
                command_obj,
                args,
                "bash",
                script_path=script_path if script_path else None,
                inline_script=inline_script if inline_script else None,
            )

        except Exception as e:
            return CommandResult(success=False, output="", error=str(e))

    def execute_node(
        self, command_obj: "Command", args: dict[str, Any]
    ) -> CommandResult:
        """Execute Node.js script command.

        Args:
            command_obj: Command object
            args: Command arguments (passed as environment variables)

        Returns:
            CommandResult with script output
        """
        from agent_arsenal.parser import (
            get_handler_info,
            parse_markdown_command,
        )

        try:
            frontmatter, _ = parse_markdown_command(command_obj.path)
            handler_info = get_handler_info(frontmatter)

            script_path = handler_info.get("path", "")
            inline_script = handler_info.get("inline", "")

            return self._execute_subprocess(
                command_obj,
                args,
                "node",
                script_path=script_path if script_path else None,
                inline_script=inline_script if inline_script else None,
            )

        except Exception as e:
            return CommandResult(success=False, output="", error=str(e))

    def execute_template(
        self, command_path: Path, args: dict[str, Any]
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
            from jinja2 import (
                BaseLoader,
                Environment,
                StrictUndefined,
                TemplateSyntaxError,
            )

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
        self,
        command: "Command",
        args: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render command instructions with argument substitution.

        Supports:
        - {{arg_name}} - Direct argument substitution
        - {{env.VAR}} - Environment variable substitution
        - {{context.key}} - Context-based substitution

        Args:
            command: Command object
            args: Command arguments
            context: Optional additional context

        Returns:
            Rendered markdown instructions
        """
        from agent_arsenal.parser import parse_markdown_command

        try:
            frontmatter, body = parse_markdown_command(command.path)
        except Exception:
            # If we can't parse, return empty
            return ""

        # Use description as instructions if available
        instructions = frontmatter.get("instructions", "")
        if not instructions:
            # Fall back to description
            instructions = frontmatter.get("description", "")

        if not instructions:
            return ""

        context = context or {}

        # Build combined context: args > context > environment
        full_context: dict[str, Any] = {}
        full_context.update(os.environ)
        full_context.update(context)
        full_context.update(args)

        # Simple template substitution using {{key}} syntax
        result = instructions
        for key, value in full_context.items():
            if value is not None:
                result = result.replace(f"{{{{{key}}}}}", str(value))

        return result


def render_instructions(
    command: "Command",
    args: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> str:
    """Standalone function to render command instructions.

    This is a convenience wrapper that creates a temporary executor
    to render instructions. For better performance, use the method
    on an existing CommandExecutor instance.

    Args:
        command: Command object
        args: Command arguments
        context: Optional additional context

    Returns:
        Rendered markdown instructions
    """
    executor = CommandExecutor()
    return executor.render_instructions(command, args, context)
