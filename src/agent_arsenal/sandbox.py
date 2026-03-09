"""Sandbox configuration and execution for secure command handling.

This module provides the core data classes and executor for running commands
within a Deno-based sandbox with configurable permissions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SandboxPermissions:
    """Permissions for sandboxed command execution."""

    allow_read: list[str] = field(default_factory=list)
    allow_write: list[str] = field(default_factory=list)
    allow_net: bool = False
    allow_env: list[str] = field(default_factory=list)
    allow_run: bool | list[str] = False


@dataclass
class SandboxConfig:
    """Global sandbox configuration."""

    enabled: bool = True
    timeout_seconds: int = 30
    backend: str = "deno"
    default_permissions: SandboxPermissions = field(default_factory=SandboxPermissions)


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


class SandboxBackend(ABC):
    """Abstract base class for sandbox backends."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config

    @abstractmethod
    def execute(
        self,
        execution_type: str,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute a script in the sandbox based on execution type."""

    @abstractmethod
    def check_available(self) -> bool:
        """Check if the backend is available on this system."""

    @abstractmethod
    def get_backend_name(self) -> str:
        """Get the name of this backend."""


class DenoSandbox(SandboxBackend):
    """Executes commands within Deno sandbox."""

    def __init__(self, config: SandboxConfig) -> None:
        super().__init__(config)
        # Common Deno installation paths to check (instance attribute for testability)
        self._deno_paths = [
            Path.home() / ".deno" / "bin" / "deno",
            Path("/usr/local/bin/deno"),
            Path("/usr/bin/deno"),
            Path.home() / "bin" / "deno",
        ]
        self._deno_path = self._detect_deno()

    def get_backend_name(self) -> str:
        """Get the name of this backend."""
        return "deno"

    def check_available(self) -> bool:
        """Check if the backend is available on this system."""
        return self._check_deno_available()

    def _detect_deno(self) -> Path | None:
        """Detect Deno installation path."""
        # First, check if deno is in PATH
        import shutil

        deno_from_path = shutil.which("deno")
        if deno_from_path:
            return Path(deno_from_path)

        # Then check common installation paths
        for path in self._deno_paths:
            if path.exists() and path.is_file():
                return path

        return None

    def _check_deno_available(self) -> bool:
        """Verify Deno is functional."""
        if self._deno_path is None:
            return False

        import subprocess

        try:
            result = subprocess.run(
                [str(self._deno_path), "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _build_permission_flags(self, permissions: SandboxPermissions) -> list[str]:
        """Map SandboxPermissions to Deno CLI flags."""
        flags = []

        if permissions.allow_read:
            if isinstance(permissions.allow_read, list):
                flags.append(f"--allow-read={','.join(permissions.allow_read)}")
            else:
                flags.append(f"--allow-read={permissions.allow_read}")

        if permissions.allow_write:
            if isinstance(permissions.allow_write, list):
                flags.append(f"--allow-write={','.join(permissions.allow_write)}")
            else:
                flags.append(f"--allow-write={permissions.allow_write}")

        if permissions.allow_net:
            flags.append("--allow-net")

        if permissions.allow_env:
            if isinstance(permissions.allow_env, list):
                flags.append(f"--allow-env={','.join(permissions.allow_env)}")
            else:
                flags.append(f"--allow-env={permissions.allow_env}")

        if permissions.allow_run:
            if isinstance(permissions.allow_run, list):
                flags.append(f"--allow-run={','.join(permissions.allow_run)}")
            else:
                flags.append("--allow-run")

        return flags

    def execute_python(
        self,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute Python script via Pyodide in Deno sandbox."""
        if permissions is None:
            permissions = self.config.default_permissions
        if timeout is None:
            timeout = self.config.timeout_seconds

        if not self._check_deno_available():
            return CommandResult(
                success=False,
                output="",
                error="Deno is not installed. Install via: curl -fsSL https://deno.land/x/install/install.sh | sh",
            )

        # Pyodide bootstrap script to run Python
        pyodide_script = (
            """
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs";
const pyodide = await loadPyodide();
const result = await pyodide.runPythonAsync(`"""
            + script
            + """`);
console.log(String(result));
"""
        )

        import subprocess
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(pyodide_script)
                script_path = f.name

            flags = self._build_permission_flags(permissions)
            cmd = [
                str(self._deno_path),
                "run",
                "--allow-read",
                "--allow-write",
                *flags,
                script_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"executor": "deno-pyodide", "exit_code": result.returncode},
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                metadata={"executor": "deno-pyodide", "timeout": True},
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                metadata={"executor": "deno-pyodide"},
            )

    def execute_bash(
        self,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute Bash script in Deno sandbox."""
        if permissions is None:
            permissions = self.config.default_permissions
        if timeout is None:
            timeout = self.config.timeout_seconds

        if not self._check_deno_available():
            return CommandResult(
                success=False,
                output="",
                error="Deno is not installed. Install via: curl -fsSL https://deno.land/x/install/install.sh | sh",
            )

        import subprocess
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                f.write(script)
                script_path = f.name

            flags = self._build_permission_flags(permissions)
            cmd = [str(self._deno_path), "run", "--allow-run", *flags, script_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"executor": "deno-bash", "exit_code": result.returncode},
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                metadata={"executor": "deno-bash", "timeout": True},
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                metadata={"executor": "deno-bash"},
            )

    def execute_node(
        self,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute Node.js script in Deno sandbox."""
        if permissions is None:
            permissions = self.config.default_permissions
        if timeout is None:
            timeout = self.config.timeout_seconds

        if not self._check_deno_available():
            return CommandResult(
                success=False,
                output="",
                error="Deno is not installed. Install via: curl -fsSL https://deno.land/x/install/install.sh | sh",
            )

        import subprocess
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(script)
                script_path = f.name

            flags = self._build_permission_flags(permissions)
            cmd = [str(self._deno_path), "run", *flags, script_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"executor": "deno-node", "exit_code": result.returncode},
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                metadata={"executor": "deno-node", "timeout": True},
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                metadata={"executor": "deno-node"},
            )

    def execute(
        self,
        execution_type: str,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute a script in the sandbox based on execution type."""
        if permissions is None:
            permissions = self.config.default_permissions
        if timeout is None:
            timeout = self.config.timeout_seconds

        if not self._check_deno_available():
            return CommandResult(
                success=False,
                output="",
                error="Deno is not installed. Install via: curl -fsSL https://deno.land/x/install/install.sh | sh",
            )

        # Route to appropriate executor based on execution type
        if execution_type == "python":
            return self.execute_python(script, permissions, timeout)
        elif execution_type == "bash":
            return self.execute_bash(script, permissions, timeout)
        elif execution_type == "node":
            return self.execute_node(script, permissions, timeout)
        else:
            return CommandResult(
                success=False,
                output="",
                error=f"Unsupported execution type: {execution_type}",
            )


# Backward compatibility alias
DenoSandboxExecutor = DenoSandbox


class LLMSandbox(SandboxBackend):
    """llm-sandbox container-based sandbox."""

    def __init__(self, config: SandboxConfig) -> None:
        super().__init__(config)
        self._docker_available: bool | None = None

    def get_backend_name(self) -> str:
        """Get the name of this backend."""
        return "llm-sandbox"

    def check_available(self) -> bool:
        """Check if the backend is available on this system (Docker running)."""
        import subprocess

        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
            )
            self._docker_available = result.returncode == 0
        except Exception:
            self._docker_available = False
        return self._docker_available

    def _map_execution_type(self, execution_type: str) -> str:
        """Map execution type to llm-sandbox language identifier."""
        mapping = {"python": "python", "node": "javascript", "javascript": "javascript"}
        return mapping.get(execution_type, "python")

    def execute(
        self,
        execution_type: str,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute a script in the llm-sandbox container."""
        if permissions is None:
            permissions = self.config.default_permissions
        if timeout is None:
            timeout = self.config.timeout_seconds

        # Lazy import to avoid errors when llm-sandbox not installed
        try:
            from llm_sandbox import SandboxSession
        except ImportError:
            return CommandResult(
                success=False,
                output="",
                error="llm-sandbox is not installed. Install with: pip install 'llm-sandbox[docker]'",
                metadata={"executor": "llm-sandbox", "import_error": True},
            )

        if not self.check_available():
            return CommandResult(
                success=False,
                output="",
                error="Docker is not running. Please start Docker and try again.",
                metadata={"executor": "llm-sandbox", "docker_unavailable": True},
            )

        lang = self._map_execution_type(execution_type)

        try:
            with SandboxSession(lang=lang) as session:
                result = session.run(script)

            return CommandResult(
                success=result.exit_code == 0,
                output=result.stdout or "",
                error=result.stderr if result.exit_code != 0 else None,
                metadata={
                    "executor": "llm-sandbox",
                    "exit_code": result.exit_code,
                    "lang": lang,
                },
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                metadata={"executor": "llm-sandbox", "exception": True},
            )


class MontySandbox(SandboxBackend):
    """Sandbox backend using pydantic-monty for secure Python execution."""

    def __init__(self, config: SandboxConfig) -> None:
        super().__init__(config)

    def get_backend_name(self) -> str:
        return "monty"

    def check_available(self) -> bool:
        try:
            import pydantic_monty  # noqa: F401

            return True
        except ImportError:
            return False

    def execute(
        self,
        execution_type: str,
        script: str,
        permissions: SandboxPermissions | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        """Execute Python code in Monty sandbox."""
        # Step 1: Validate execution_type
        if execution_type != "python":
            return CommandResult(
                success=False,
                output="",
                error=f"MontySandbox only supports execution_type='python', got '{execution_type}'",
                metadata={"executor": "monty", "error_type": "unsupported_type"},
            )

        # Step 2: Lazy import Monty components
        try:
            from pydantic_monty import (
                Monty,
                MontyError,
                MontyRuntimeError,
                MontySyntaxError,
                ResourceLimits,
            )
        except ImportError:
            return CommandResult(
                success=False,
                output="",
                error="pydantic-monty is not installed. Install with: pip install pydantic-monty",
                metadata={"executor": "monty", "import_error": True},
            )

        # Step 3: Resolve timeout
        effective_timeout = (
            timeout if timeout is not None else self.config.timeout_seconds
        )

        # Step 4: Build ResourceLimits
        limits = ResourceLimits(max_duration_secs=effective_timeout)

        # Step 5: Build output capture callback
        output_parts: list[str] = []

        def _capture_output(stream: str, text: str) -> None:
            output_parts.append(text)

        # Step 6: Execute the script
        try:
            monty = Monty(script)
            result = monty.run(print_callback=_capture_output, limits=limits)
        except Exception as e:
            # Collect any partial output
            partial_output = "".join(output_parts)

            # Step 8: Handle exceptions
            if isinstance(e, MontySyntaxError):
                return CommandResult(
                    success=False,
                    output=partial_output,
                    error=str(e),
                    metadata={"executor": "monty", "error_type": "syntax"},
                )
            elif isinstance(e, MontyRuntimeError):
                metadata: dict = {"executor": "monty", "error_type": "runtime"}
                if "TimeoutError" in str(e) and "time limit" in str(e):
                    metadata["timeout"] = True
                return CommandResult(
                    success=False,
                    output=partial_output,
                    error=str(e),
                    metadata=metadata,
                )
            elif isinstance(e, MontyError):
                return CommandResult(
                    success=False,
                    output=partial_output,
                    error=str(e),
                    metadata={"executor": "monty", "error_type": "monty"},
                )
            else:
                return CommandResult(
                    success=False,
                    output=partial_output,
                    error=str(e),
                    metadata={"executor": "monty", "error_type": "unexpected"},
                )

        # Step 7: Success handling
        output = "".join(output_parts)
        if result is not None and output.strip() == "":
            output = str(result)

        return CommandResult(
            success=True,
            output=output,
            metadata={"executor": "monty"},
        )


def get_sandbox_backend(config: SandboxConfig) -> SandboxBackend:
    """Factory function to create a sandbox backend based on configuration."""
    if config.backend == "llm-sandbox":
        return LLMSandbox(config)
    elif config.backend == "deno":
        return DenoSandbox(config)
    elif config.backend == "monty":
        return MontySandbox(config)
    else:
        raise ValueError(f"Unknown sandbox backend: {config.backend}")
