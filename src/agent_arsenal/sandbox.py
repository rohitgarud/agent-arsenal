"""Sandbox configuration and execution for secure command handling.

This module provides the core data classes and executor for running commands
within a Deno-based sandbox with configurable permissions.
"""

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


class DenoSandboxExecutor:
    """Executes commands within Deno sandbox."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config
        # Common Deno installation paths to check (instance attribute for testability)
        self._deno_paths = [
            Path.home() / ".deno" / "bin" / "deno",
            Path("/usr/local/bin/deno"),
            Path("/usr/bin/deno"),
            Path.home() / "bin" / "deno",
        ]
        self._deno_path = self._detect_deno()

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
