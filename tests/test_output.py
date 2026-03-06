"""Tests for output.py - OutputManager and OutputConfig."""

import json
import sys
from unittest.mock import patch

from agent_arsenal.output import OutputConfig, OutputManager, get_output_manager


class TestOutputConfig:
    """Tests for OutputConfig dataclass."""

    def test_default_values(self):
        """Test OutputConfig has correct default values."""
        config = OutputConfig()
        assert config.quiet is False
        assert config.verbose is False
        assert config.no_color is False

    def test_custom_values(self):
        """Test OutputConfig with custom values."""
        config = OutputConfig(quiet=True, verbose=True, no_color=True)
        assert config.quiet is True
        assert config.verbose is True
        assert config.no_color is True

    def test_partial_custom_values(self):
        """Test OutputConfig with some custom values."""
        config = OutputConfig(quiet=True)
        assert config.quiet is True
        assert config.verbose is False
        assert config.no_color is False


class TestOutputManager:
    """Tests for OutputManager class."""

    def test_initialization_with_defaults(self):
        """Test OutputManager initializes with default config."""
        config = OutputConfig()
        manager = OutputManager(config)
        assert manager.config == config
        assert manager.is_quiet is False
        assert manager.is_verbose is False

    def test_initialization_with_quiet_mode(self):
        """Test OutputManager in quiet mode."""
        config = OutputConfig(quiet=True)
        manager = OutputManager(config)
        assert manager.is_quiet is True
        assert manager.is_verbose is False

    def test_initialization_with_verbose_mode(self):
        """Test OutputManager in verbose mode."""
        config = OutputConfig(verbose=True)
        manager = OutputManager(config)
        assert manager.is_quiet is False
        assert manager.is_verbose is True

    def test_print_result_outputs_content_to_console(self):
        """Test print_result outputs content via Rich Console."""
        from agent_arsenal.executor import CommandResult

        config = OutputConfig()
        manager = OutputManager(config)
        result = CommandResult(success=True, output="hello world")
        with patch.object(manager._console_stdout, "print") as mock_print:
            manager.print_result(result)
            mock_print.assert_called_once_with("hello world")

    def test_print_result_quiet_mode_uses_plain_print(self):
        """Test print_result in quiet mode uses built-in print."""
        from agent_arsenal.executor import CommandResult

        config = OutputConfig(quiet=True)
        manager = OutputManager(config)
        result = CommandResult(success=True, output="quiet result")
        # In quiet mode, should use built-in print which we can capture
        with patch("builtins.print") as mock_print:
            manager.print_result(result)
            mock_print.assert_called_once_with("quiet result", file=sys.stdout)

    def test_print_error_outputs_to_console(self):
        """Test print_error outputs to stderr via Rich Console."""
        config = OutputConfig()
        manager = OutputManager(config)
        with patch.object(manager._console_stderr, "print") as mock_print:
            manager.print_error("something went wrong")
            mock_print.assert_called_once_with("[error]Error:[/error] something went wrong")

    def test_print_error_quiet_mode_uses_plain_print(self):
        """Test print_error in quiet mode uses built-in print to stderr."""
        config = OutputConfig(quiet=True)
        manager = OutputManager(config)
        with patch("builtins.print") as mock_print:
            manager.print_error("error in quiet mode")
            mock_print.assert_called_once_with("error in quiet mode", file=sys.stderr)

    def test_print_verbose_suppressed_in_quiet_mode(self):
        """Test print_verbose is suppressed in quiet mode."""
        config = OutputConfig(quiet=True, verbose=True)
        manager = OutputManager(config)
        with patch("builtins.print") as mock_print:
            manager.print_verbose("verbose message")
            mock_print.assert_not_called()

    def test_print_verbose_works_when_not_quiet(self):
        """Test print_verbose works when quiet=False."""
        config = OutputConfig(verbose=True, quiet=False)
        manager = OutputManager(config)
        with patch.object(manager._console_stderr, "print") as mock_print:
            manager.print_verbose("verbose message")
            mock_print.assert_called_once_with("[verbose]verbose message[/verbose]")

    def test_print_verbose_suppressed_when_verbose_false(self):
        """Test print_verbose is suppressed when verbose=False."""
        config = OutputConfig(verbose=False)
        manager = OutputManager(config)
        with patch.object(manager._console_stderr, "print") as mock_print:
            manager.print_verbose("should not appear")
            mock_print.assert_not_called()

    def test_print_banner_suppressed_in_quiet_mode(self):
        """Test print_banner is suppressed in quiet mode."""
        config = OutputConfig(quiet=True)
        manager = OutputManager(config)
        with patch("builtins.print") as mock_print:
            manager.print_banner("Banner text")
            mock_print.assert_not_called()

    def test_print_banner_works_when_not_quiet(self):
        """Test print_banner works when quiet=False."""
        config = OutputConfig(quiet=False)
        manager = OutputManager(config)
        with patch.object(manager._console_stdout, "print") as mock_print:
            manager.print_banner("Banner text")
            mock_print.assert_called_once_with("Banner text")

    def test_print_info_suppressed_in_quiet_mode(self):
        """Test print_info is suppressed in quiet mode."""
        config = OutputConfig(quiet=True)
        manager = OutputManager(config)
        with patch("builtins.print") as mock_print:
            manager.print_info("info message")
            mock_print.assert_not_called()

    def test_print_info_works_when_not_quiet(self):
        """Test print_info works when quiet=False."""
        config = OutputConfig(quiet=False)
        manager = OutputManager(config)
        with patch.object(manager._console_stdout, "print") as mock_print:
            manager.print_info("info message")
            mock_print.assert_called_once_with("[info]info message[/info]")


class TestJsonOutput:
    """Tests for JSON output functionality in OutputManager."""

    def test_print_result_json_success(self):
        """Test print_result outputs valid JSON for successful command."""
        from agent_arsenal.executor import CommandResult

        config = OutputConfig(json=True)
        manager = OutputManager(config)
        result = CommandResult(success=True, output="test output")

        with patch("typer.echo") as mock_echo:
            manager.print_result(result)
            mock_echo.assert_called_once()
            output = mock_echo.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["success"] is True
            assert parsed["output"] == "test output"
            assert parsed["error"] is None

    def test_print_result_json_error(self):
        """Test print_result outputs valid JSON for failed command."""
        from agent_arsenal.executor import CommandResult

        config = OutputConfig(json=True)
        manager = OutputManager(config)
        result = CommandResult(success=False, output="", error="Something failed")

        with patch("typer.echo") as mock_echo:
            manager.print_result(result)
            mock_echo.assert_called_once()
            output = mock_echo.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["success"] is False
            assert parsed["output"] == ""
            assert parsed["error"] == "Something failed"

    def test_print_result_json_with_metadata(self):
        """Test print_result includes metadata in JSON output when present."""
        from agent_arsenal.executor import CommandResult

        config = OutputConfig(json=True)
        manager = OutputManager(config)
        result = CommandResult(
            success=True,
            output="result data",
            metadata={"command": "uuid", "duration_ms": 42}
        )

        with patch("typer.echo") as mock_echo:
            manager.print_result(result)
            mock_echo.assert_called_once()
            output = mock_echo.call_args[0][0]
            parsed = json.loads(output)
            assert "metadata" in parsed
            assert parsed["metadata"]["command"] == "uuid"
            assert parsed["metadata"]["duration_ms"] == 42

    def test_print_error_json(self):
        """Test print_error outputs error in JSON format when json=True."""
        config = OutputConfig(json=True)
        manager = OutputManager(config)

        with patch("typer.echo") as mock_echo:
            manager.print_error("Something went wrong")
            mock_echo.assert_called_once()
            output = mock_echo.call_args[0][0]
            parsed = json.loads(output)
            assert parsed["success"] is False
            assert parsed["output"] == ""
            assert parsed["error"] == "Something went wrong"

    def test_json_flag_defaults_to_false(self):
        """Test OutputConfig json field defaults to False."""
        config = OutputConfig()
        assert config.json is False

    def test_json_flag_can_be_set_true(self):
        """Test OutputConfig json field can be set to True."""
        config = OutputConfig(json=True)
        assert config.json is True


class TestGetOutputManager:
    """Tests for get_output_manager function."""

    def test_returns_default_manager(self):
        """Test get_output_manager returns a default manager."""
        manager = get_output_manager()
        assert isinstance(manager, OutputManager)

    def test_returns_manager_with_config(self):
        """Test get_output_manager with custom config."""
        config = OutputConfig(quiet=True)
        manager = get_output_manager(config)
        assert isinstance(manager, OutputManager)
        assert manager.is_quiet is True

    def test_same_instance_for_default(self):
        """Test default manager is reused."""
        manager1 = get_output_manager()
        manager2 = get_output_manager()
        assert manager1 is manager2

    def test_different_instances_for_custom_config(self):
        """Test custom config creates new instance."""
        config = OutputConfig(quiet=True)
        manager1 = get_output_manager(config)
        config2 = OutputConfig(quiet=False)
        manager2 = get_output_manager(config2)
        assert manager1 is not manager2


class TestQuietFlagIntegration:
    """Integration tests for --quiet flag in CLI."""

    def test_quiet_flag_in_help(self, cli_runner):
        """Test --quiet flag appears in help output."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--help"])
        assert "--quiet" in result.output
        assert "-q" in result.output

    def test_quiet_flag_works(self, cli_runner):
        """Test --quiet flag executes command successfully."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--quiet", "common", "uuid"])
        # Verify command runs without error
        assert result.exit_code == 0

    def test_q_short_alias_works(self, cli_runner):
        """Test -q short alias works."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["-q", "common", "uuid"])
        assert result.exit_code == 0

    def test_quiet_help_still_works(self, cli_runner):
        """Test --quiet --help shows help without breaking."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--quiet", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_quiet_verbose_precedence(self, cli_runner):
        """Test --quiet takes precedence over --verbose."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--quiet", "--verbose", "common", "uuid"])
        # Should run successfully - quiet takes precedence
        assert result.exit_code == 0

    def test_no_color_flag_in_help(self, cli_runner):
        """Test --no-color flag appears in help output."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--help"])
        assert "--no-color" in result.output

    def test_no_color_flag_works(self, cli_runner):
        """Test --no-color flag works."""
        from agent_arsenal.main import app
        result = cli_runner.invoke(app, ["--no-color", "common", "uuid"])
        assert result.exit_code == 0


class TestExecutorOutputManagerIntegration:
    """Tests for OutputManager integration in CommandExecutor."""

    def test_executor_accepts_output_manager(self):
        """Test CommandExecutor accepts OutputManager in constructor."""
        from agent_arsenal.executor import CommandExecutor
        from agent_arsenal.output import OutputConfig, OutputManager

        config = OutputConfig(verbose=True)
        manager = OutputManager(config)
        executor = CommandExecutor(manager)

        assert executor._output_manager is manager

    def test_executor_output_manager_none_by_default(self):
        """Test CommandExecutor defaults to no OutputManager."""
        from agent_arsenal.executor import CommandExecutor

        executor = CommandExecutor()
        assert executor._output_manager is None

    def test_executor_print_verbose_with_output_manager(self):
        """Test executor uses OutputManager for verbose output."""
        from agent_arsenal.executor import CommandExecutor
        from agent_arsenal.output import OutputConfig, OutputManager

        config = OutputConfig(verbose=True)
        manager = OutputManager(config)
        executor = CommandExecutor(manager)

        with patch.object(manager, "print_verbose") as mock_print:
            executor._print_verbose("test message")
            mock_print.assert_called_once_with("test message")

    def test_executor_calls_print_verbose_always(self):
        """Test executor always calls print_verbose on OutputManager.

        The OutputManager internally decides whether to actually print
        based on quiet/verbose settings.
        """
        from agent_arsenal.executor import CommandExecutor
        from agent_arsenal.output import OutputConfig, OutputManager

        config = OutputConfig(quiet=True, verbose=True)
        manager = OutputManager(config)
        executor = CommandExecutor(manager)

        # Executor should still call print_verbose - OutputManager handles suppression
        with patch.object(manager, "print_verbose") as mock_print:
            executor._print_verbose("test message")
            mock_print.assert_called_once_with("test message")

    def test_executor_fallback_to_legacy_verbose(self):
        """Test executor falls back to legacy verbose mode when no OutputManager."""
        from agent_arsenal import executor as executor_module
        from agent_arsenal.executor import CommandExecutor

        # Ensure module-level verbose is True
        with patch("agent_arsenal.executor._verbose_mode", True):
            with patch.object(executor_module, "console_stderr") as mock_console:
                mock_print = patch.object(mock_console, "print").start()
                executor_instance = CommandExecutor()
                executor_instance._print_verbose("test message")
                mock_print.assert_called_once()
                mock_print.stop()

    def test_executor_with_quiet_output_manager(self):
        """Test executor calls OutputManager which handles quiet internally."""
        from agent_arsenal.executor import CommandExecutor
        from agent_arsenal.output import OutputConfig, OutputManager

        config = OutputConfig(quiet=True, verbose=True)
        manager = OutputManager(config)
        executor = CommandExecutor(manager)

        # When quiet=True, OutputManager.print_verbose returns early internally
        # but the executor still makes the call
        with patch.object(manager, "print_verbose") as mock_print:
            executor._print_verbose("verbose message")
            # The executor delegates to OutputManager, which handles quiet internally
            mock_print.assert_called_once_with("verbose message")
