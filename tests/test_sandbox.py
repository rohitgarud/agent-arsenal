"""Tests for sandbox module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from agent_arsenal.sandbox import (
    CommandResult,
    DenoSandboxExecutor,
    SandboxConfig,
    SandboxPermissions,
)


class TestSandboxPermissions:
    """Tests for SandboxPermissions dataclass."""

    def test_default_instantiation(self):
        """Test SandboxPermissions with default values."""
        perms = SandboxPermissions()
        assert perms.allow_read == []
        assert perms.allow_write == []
        assert perms.allow_net is False
        assert perms.allow_env == []
        assert perms.allow_run is False

    def test_custom_permissions(self):
        """Test SandboxPermissions accepts all permission fields."""
        perms = SandboxPermissions(
            allow_read=["/tmp", "/home"],
            allow_write=["/tmp"],
            allow_net=True,
            allow_env=["HOME", "PATH"],
            allow_run=["npm", "node"],
        )
        assert perms.allow_read == ["/tmp", "/home"]
        assert perms.allow_write == ["/tmp"]
        assert perms.allow_net is True
        assert perms.allow_env == ["HOME", "PATH"]
        assert perms.allow_run == ["npm", "node"]

    def test_allow_run_as_bool(self):
        """Test allow_run accepts boolean value."""
        perms = SandboxPermissions(allow_run=True)
        assert perms.allow_run is True

    def test_allow_run_as_list(self):
        """Test allow_run accepts list of strings."""
        perms = SandboxPermissions(allow_run=["bash", "python"])
        assert perms.allow_run == ["bash", "python"]


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_instantiation(self):
        """Test SandboxConfig with default values."""
        config = SandboxConfig()
        assert config.enabled is True
        assert config.timeout_seconds == 30
        assert isinstance(config.default_permissions, SandboxPermissions)

    def test_custom_config(self):
        """Test SandboxConfig accepts custom values."""
        perms = SandboxPermissions(allow_read=["/home"])
        config = SandboxConfig(
            enabled=False,
            timeout_seconds=60,
            default_permissions=perms,
        )
        assert config.enabled is False
        assert config.timeout_seconds == 60
        assert config.default_permissions.allow_read == ["/home"]


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_basic_instantiation(self):
        """Test CommandResult with required fields."""
        result = CommandResult(success=True, output="hello")
        assert result.success is True
        assert result.output == "hello"
        assert result.error is None
        assert result.metadata == {}

    def test_full_instantiation(self):
        """Test CommandResult with all fields."""
        metadata = {"duration": 1.5, "exit_code": 0}
        result = CommandResult(
            success=True,
            output="output",
            error=None,
            metadata=metadata,
        )
        assert result.success is True
        assert result.output == "output"
        assert result.metadata == metadata

    def test_failure_result(self):
        """Test CommandResult for failure case."""
        result = CommandResult(
            success=False,
            output="",
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"


class TestDenoSandboxExecutor:
    """Tests for DenoSandboxExecutor class."""

    def test_init_with_default_config(self):
        """Test executor initializes with default config."""
        executor = DenoSandboxExecutor(SandboxConfig())
        assert executor.config.enabled is True
        assert executor.config.timeout_seconds == 30

    @patch("shutil.which")
    def test_detect_deno_in_path(self, mock_which):
        """Test _detect_deno finds Deno in PATH."""
        mock_which.return_value = "/usr/bin/deno"
        executor = DenoSandboxExecutor(SandboxConfig())
        result = executor._detect_deno()
        assert result == Path("/usr/bin/deno")

    @patch("shutil.which")
    def test_detect_deno_when_not_in_path(self, mock_which):
        """Test _detect_deno returns None when Deno not found anywhere."""
        mock_which.return_value = None  # Not in PATH

        # Create executor first
        executor = DenoSandboxExecutor(SandboxConfig())

        # Mock _deno_paths to contain non-existent paths
        non_existent_paths = [
            Path("/nonexistent/path1/deno"),
            Path("/nonexistent/path2/deno"),
        ]
        executor._deno_paths = non_existent_paths

        result = executor._detect_deno()
        assert result is None

    @patch("shutil.which")
    @patch("agent_arsenal.sandbox.Path.exists")
    def test_detect_deno_not_found(self, mock_exists, mock_which):
        """Test _detect_deno returns None when Deno not found."""
        mock_which.return_value = None
        mock_exists.return_value = False

        executor = DenoSandboxExecutor(SandboxConfig())
        result = executor._detect_deno()
        assert result is None

    def test_build_permission_flags_empty(self):
        """Test _build_permission_flags with no permissions."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions()
        flags = executor._build_permission_flags(perms)
        assert flags == []

    def test_build_permission_flags_read(self):
        """Test _build_permission_flags for allow_read."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_read=["/tmp", "/home"])
        flags = executor._build_permission_flags(perms)
        assert "--allow-read=/tmp,/home" in flags

    def test_build_permission_flags_write(self):
        """Test _build_permission_flags for allow_write."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_write=["/tmp"])
        flags = executor._build_permission_flags(perms)
        assert "--allow-write=/tmp" in flags

    def test_build_permission_flags_net(self):
        """Test _build_permission_flags for allow_net."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_net=True)
        flags = executor._build_permission_flags(perms)
        assert "--allow-net" in flags

    def test_build_permission_flags_env(self):
        """Test _build_permission_flags for allow_env."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_env=["HOME", "PATH"])
        flags = executor._build_permission_flags(perms)
        assert "--allow-env=HOME,PATH" in flags

    def test_build_permission_flags_run_bool(self):
        """Test _build_permission_flags for allow_run as bool."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_run=True)
        flags = executor._build_permission_flags(perms)
        assert "--allow-run" in flags

    def test_build_permission_flags_run_list(self):
        """Test _build_permission_flags for allow_run as list."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(allow_run=["bash", "python"])
        flags = executor._build_permission_flags(perms)
        assert "--allow-run=bash,python" in flags

    def test_build_permission_flags_multiple(self):
        """Test _build_permission_flags with multiple permissions."""
        executor = DenoSandboxExecutor(SandboxConfig())
        perms = SandboxPermissions(
            allow_read=["/tmp"],
            allow_write=["/tmp"],
            allow_net=True,
            allow_env=["HOME"],
            allow_run=["bash"],
        )
        flags = executor._build_permission_flags(perms)
        assert len(flags) == 5
        assert "--allow-read=/tmp" in flags
        assert "--allow-write=/tmp" in flags
        assert "--allow-net" in flags
        assert "--allow-env=HOME" in flags
        assert "--allow-run=bash" in flags


def has_deno() -> bool:
    """Check if Deno is installed on the system."""
    import shutil
    from pathlib import Path

    # Check PATH first
    if shutil.which("deno") is not None:
        return True

    # Check common installation paths
    deno_paths = [
        Path.home() / ".deno" / "bin" / "deno",
        Path("/usr/local/bin/deno"),
        Path("/usr/bin/deno"),
        Path.home() / "bin" / "deno",
    ]

    for path in deno_paths:
        if path.exists() and path.is_file():
            return True

    return False


@pytest.mark.skipif(not has_deno(), reason="Deno not installed")
class TestDenoSandboxExecutorIntegration:
    """Integration tests for DenoSandboxExecutor (requires Deno)."""

    def test_check_deno_available(self):
        """Test _check_deno_available returns True when Deno is installed."""
        executor = DenoSandboxExecutor(SandboxConfig())
        assert executor._check_deno_available() is True

    def test_execute_unsupported_type(self):
        """Test execute with unsupported execution type."""
        executor = DenoSandboxExecutor(SandboxConfig())
        result = executor.execute("unsupported", "echo hello")
        assert result.success is False
        assert "Unsupported execution type" in result.error
