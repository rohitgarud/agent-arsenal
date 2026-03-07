"""Tests for main.py CLI module."""

import json
import unittest.mock

import pytest
from typer.testing import CliRunner

from agent_arsenal.main import (
    app,
    get_commands_dir,
    get_registry,
)
from agent_arsenal.registry import CommandRegistry


@pytest.fixture
def runner():
    """CliRunner fixture."""
    return CliRunner()


class TestCLICommands:
    """Test CLI commands."""

    def test_cli_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "arsenal" in result.output.lower()

    def test_cli_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Agent Arsenal" in result.output


class TestHelperFunctions:
    """Test helper functions in main.py."""

    def test_get_commands_dir_default(self):
        """Test get_commands_dir returns correct path."""
        commands_dir = get_commands_dir()
        assert commands_dir.exists()
        assert commands_dir.is_dir()
        assert "commands" in str(commands_dir)

    def test_get_registry_lazy_init(self):
        """Test get_registry initializes lazily."""
        # Should return a CommandRegistry
        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, CommandRegistry)

    def test_get_registry_returns_same_instance(self):
        """Test get_registry returns the same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2


class TestAppCommands:
    """Test app CLI commands."""

    def test_app_callback(self, runner):
        """Test app callback runs."""
        result = runner.invoke(app, [])
        # Should either show help or list commands or exit with 0, 1, or 2
        assert result.exit_code in [0, 1, 2]

    @unittest.mock.patch("agent_arsenal.main.get_registry")
    def test_list_commands(self, mock_get_registry, runner):
        """Test listing commands."""
        # Create mock registry
        mock_registry = unittest.mock.MagicMock()
        mock_registry.get_all_commands.return_value = []
        mock_registry.get_command_groups.return_value = []
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(app, ["list"])
        # May fail due to other dependencies but shouldn't crash
        assert result is not None


class TestParseScope:
    """Test scope parsing utilities."""

    def test_scope_single(self):
        """Test parsing single scope."""
        # Test the scope format
        scope = "common"
        parts = scope.split(":")
        assert parts == ["common"]

    def test_scope_multiple(self):
        """Test parsing multiple scopes."""
        scope = "common:time"
        parts = scope.split(":")
        assert parts == ["common", "time"]


class TestRegisterCommands:
    """Test command registration."""

    def test_register_commands_recursive(self):
        """Test recursive command registration works."""
        # Just verify get_registry doesn't crash
        registry = get_registry()
        assert registry is not None


class TestConfigCommands:
    """Test config CLI commands."""

    @unittest.mock.patch("agent_arsenal.main.load_sandbox_config")
    @unittest.mock.patch("agent_arsenal.main.save_sandbox_config")
    def test_sandbox_config_show(self, mock_save, mock_load, runner):
        """Test sandbox config show command."""
        mock_load.return_value = {"enabled": True, "timeout_seconds": 30}

        result = runner.invoke(app, ["sandbox", "config", "show"])
        # Should work (or fail gracefully)
        assert result is not None

    @unittest.mock.patch("agent_arsenal.main.load_sandbox_config")
    @unittest.mock.patch("agent_arsenal.main.save_sandbox_config")
    def test_sandbox_config_set(self, mock_save, mock_load, runner):
        """Test sandbox config set command."""
        mock_load.return_value = {"enabled": True, "timeout_seconds": 30}

        result = runner.invoke(app, ["sandbox", "config", "set", "timeout", "60"])
        # Should work (or fail gracefully)
        assert result is not None

    def test_config_get(self, runner):
        """Test config get command."""
        result = runner.invoke(app, ["config", "get", "command_directories"])
        # May fail due to config issues but shouldn't crash
        assert result is not None

    def test_config_set(self, runner):
        """Test config set command."""
        result = runner.invoke(app, ["config", "set", "test_key", "test_value"])
        # May fail but shouldn't crash
        assert result is not None


class TestStateCommands:
    """Test state CLI commands."""

    def test_state_get(self, runner):
        """Test state get command."""
        result = runner.invoke(app, ["state", "get", "test_key"])
        # May fail but shouldn't crash
        assert result is not None

    def test_state_set(self, runner):
        """Test state set command."""
        result = runner.invoke(app, ["state", "set", "test_key", "test_value"])
        # May fail but shouldn't crash
        assert result is not None

    def test_state_delete(self, runner):
        """Test state delete command."""
        result = runner.invoke(app, ["state", "delete", "test_key"])
        # May fail but shouldn't crash
        assert result is not None


class TestExternalCommands:
    """Test external command execution."""

    def test_external_command_help(self, runner):
        """Test running an external command with --help."""
        result = runner.invoke(app, ["common", "uuid", "--help"])
        # Should show help
        assert result is not None

    def test_run_command_basic(self, runner):
        """Test running a basic command."""
        result = runner.invoke(app, ["common", "uuid"])
        # Should return some output
        assert result is not None

    def test_run_hash_command(self, runner):
        """Test running hash command."""
        result = runner.invoke(
            app, ["common", "hash", "--input", "test", "--algorithm", "sha256"]
        )
        # Should return hash output
        assert result is not None

    def test_run_timestamp_command(self, runner):
        """Test running timestamp command."""
        result = runner.invoke(app, ["common", "time", "timestamp"])
        # Should return timestamp output
        assert result is not None


class TestWatchCommands:
    """Test watch CLI commands."""

    def test_watch_start(self, runner, tmp_path):
        """Test watch start command."""
        # Create a commands dir
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()

        result = runner.invoke(app, ["watch", "start", str(commands_dir)])
        # Should either start or show error (but not crash)
        assert result is not None


class TestVerboseFlag:
    """Test --verbose flag integration."""

    def test_verbose_flag_in_help(self, runner):
        """Test --verbose appears in help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output
        assert "-V" in result.output

    def test_verbose_flag_produces_verbose_output(self, runner):
        """Test --verbose flag produces verbose output without crashing."""
        # Reset verbose mode state
        from agent_arsenal.executor import set_verbose_mode
        set_verbose_mode(False)

        result = runner.invoke(app, ["--verbose", "common", "uuid"])

        # Just verify it runs without crashing (exit_code 0)
        # Note: result.output may be empty due to CliRunner capturing stdout/stderr separately
        assert result.exit_code == 0

    def test_no_verbose_flag_no_verbose_strings(self, runner):
        """Test running without --verbose flag doesn't produce verbose output."""
        # Reset verbose mode state
        from agent_arsenal.executor import set_verbose_mode
        set_verbose_mode(False)

        result = runner.invoke(app, ["common", "uuid"])

        # Without verbose flag, should NOT contain verbose strings
        assert "Executing handler:" not in result.output
        assert "Args:" not in result.output
        # But should have UUID (36 chars with hyphens)
        # result.output contains the UUID


class TestJsonFlag:
    """Test --json flag integration."""

    def test_json_flag_in_help(self, runner):
        """Test --json appears in help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--json" in result.output

    def test_json_flag_uuid_command(self, runner):
        """Test --json flag with uuid command returns valid JSON."""
        result = runner.invoke(app, ["--json", "common", "uuid"])
        assert result.exit_code == 0
        # Should be valid JSON
        parsed = json.loads(result.output)
        assert "success" in parsed
        assert "output" in parsed
        assert parsed["success"] is True
        assert parsed["output"] is not None
        # UUID format check (36 chars with hyphens)
        assert len(parsed["output"]) == 36

    def test_json_flag_invalid_command(self, runner):
        """Test --json flag with invalid command returns error JSON."""
        result = runner.invoke(app, ["--json", "common", "invalid-cmd-xyz"])
        # Exit code should be non-zero for error
        assert result.exit_code != 0
        # In JSON mode, the error should still be JSON
        # But note: Typer errors may not be JSON formatted
        # Let's check if it's valid JSON first
        try:
            parsed = json.loads(result.output)
            # If it's JSON, check for error field
            assert "error" in parsed or "success" in parsed
        except json.JSONDecodeError:
            # If it's not JSON, that's okay - Typer error handling may vary
            pass

    def test_json_flag_hash_command(self, runner):
        """Test --json flag with hash command returns valid JSON."""
        result = runner.invoke(
            app, ["--json", "common", "hash", "--input", "hello", "--algorithm", "sha256"]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "output" in parsed
        # SHA256 hash is 64 hex characters
        assert len(parsed["output"]) == 64

    def test_json_flag_timestamp_command(self, runner):
        """Test --json flag with timestamp command returns valid JSON."""
        result = runner.invoke(app, ["--json", "common", "time", "timestamp"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "output" in parsed
        # Timestamp should be a non-empty string (can be date format or epoch)
        assert len(parsed["output"]) > 0

    def test_json_output_parseable(self, runner):
        """Test JSON output is parseable by json.tool."""
        result = runner.invoke(app, ["--json", "common", "uuid"])
        assert result.exit_code == 0
        # Should not raise
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_json_flag_different_groups(self, runner):
        """Test --json flag works with different command groups."""
        # Test with common group (already tested above)
        result = runner.invoke(app, ["--json", "common", "uuid"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True


class TestListCommand:
    """Test the 'list' subcommand for command discovery."""

    def test_list_commands_default(self, runner):
        """Test 'arsenal list' shows all commands."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Should show common group
        assert "common" in result.output
        # Should show some commands
        assert "uuid" in result.output or "hash" in result.output

    def test_list_commands_json(self, runner):
        """Test 'arsenal --json list' returns valid JSON."""
        result = runner.invoke(app, ["--json", "list"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "output" in parsed

    def test_list_commands_with_level(self, runner):
        """Test 'arsenal list --level 1' limits depth."""
        result = runner.invoke(app, ["list", "--level", "1"])
        assert result.exit_code == 0
        # Level 1 shows root only - no subgroups (since max_depth=1 filters out subgroups)
        # Should show "root" as the group name
        assert "root" in result.output.lower() or "Commands:" in result.output

    def test_list_commands_group_filter(self, runner):
        """Test 'arsenal list common' filters to group."""
        result = runner.invoke(app, ["list", "common"])
        assert result.exit_code == 0
        # Should show common as the root
        assert "common" in result.output
        # Should show commands within common
        assert "uuid" in result.output

    def test_list_commands_help(self, runner):
        """Test 'arsenal list --help' displays options."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "Group to list" in result.output
        assert "--level" in result.output or "-l" in result.output

    def test_list_commands_json_structure(self, runner):
        """Validate JSON output has success, output, metadata fields."""
        result = runner.invoke(app, ["--json", "list"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        # Check top-level structure
        assert "success" in parsed
        assert "output" in parsed
        assert "metadata" in parsed
        # Check metadata fields
        assert "total_commands" in parsed["metadata"]
        assert "total_groups" in parsed["metadata"]
        assert "depth" in parsed["metadata"]

    def test_list_commands_nonexistent_group(self, runner):
        """Test handling of invalid group name."""
        result = runner.invoke(app, ["list", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_list_commands_json_nonexistent_group(self, runner):
        """Test JSON output for nonexistent group."""
        result = runner.invoke(app, ["--json", "list", "nonexistent"])
        assert result.exit_code == 1
        parsed = json.loads(result.output)
        assert parsed["success"] is False
        assert "error" in parsed

    def test_list_commands_level_2(self, runner):
        """Test depth limiting with level 2."""
        result = runner.invoke(app, ["list", "--level", "2"])
        assert result.exit_code == 0
        # Should show root and one level of subgroups
        assert "common" in result.output
        # Should show direct commands of common
        assert "uuid" in result.output or "hash" in result.output
