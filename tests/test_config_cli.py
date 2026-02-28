"""Tests for the config CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

# Import app at module level - tests will need to handle isolation
from agent_arsenal.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_cli_state(monkeypatch, tmp_path):
    """Reset CLI state for each test."""
    # Mock get_config_path to use temp directory
    config_file = tmp_path / ".arsenal" / "settings.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    import agent_arsenal.config as config_module

    monkeypatch.setattr(config_module, "get_config_path", lambda: config_file)

    # Mock get_command_directories to return empty
    import agent_arsenal.main as main_module

    monkeypatch.setattr(main_module, "get_command_directories", lambda: [])


class TestExternalDirAdd:
    """Tests for 'arsenal config external-dir add' command."""

    def test_adds_directory(self, temp_dir: Path):
        """Should add a directory to config."""
        result = runner.invoke(
            app, ["config", "external-dir", "add", str(temp_dir / "new-dir")]
        )
        assert result.exit_code == 0
        assert "Added:" in result.output

    def test_shows_already_registered_for_duplicate(self, temp_dir: Path):
        """Should show 'Already registered' for duplicate."""
        test_dir = temp_dir / "dup-dir"
        test_dir.mkdir()

        # First add
        runner.invoke(app, ["config", "external-dir", "add", str(test_dir)])
        # Second add
        result = runner.invoke(app, ["config", "external-dir", "add", str(test_dir)])

        assert result.exit_code == 0
        assert "Already registered" in result.output


class TestExternalDirRemove:
    """Tests for 'arsenal config external-dir remove' command."""

    def test_removes_directory(self, temp_dir: Path):
        """Should remove a directory from config."""
        test_dir = temp_dir / "to-remove"
        test_dir.mkdir()

        # Add first
        runner.invoke(app, ["config", "external-dir", "add", str(test_dir)])
        # Then remove
        result = runner.invoke(app, ["config", "external-dir", "remove", str(test_dir)])

        assert result.exit_code == 0
        assert "Removed:" in result.output

    def test_shows_not_found_for_nonexistent(self, temp_dir: Path):
        """Should show 'Not found' for non-existent directory."""
        result = runner.invoke(
            app,
            ["config", "external-dir", "remove", str(temp_dir / "nonexistent")],
        )

        assert result.exit_code == 0
        assert "Not found" in result.output


class TestExternalDirList:
    """Tests for 'arsenal config external-dir list' command."""

    def test_shows_empty_message_when_none(self):
        """Should show message when no directories."""
        result = runner.invoke(app, ["config", "external-dir", "list"])

        assert result.exit_code == 0
        assert "No external command directories registered" in result.output

    def test_lists_directories(self, temp_dir: Path):
        """Should list all registered directories."""
        test_dir = temp_dir / "list-test"
        test_dir.mkdir()

        # Add a directory
        runner.invoke(app, ["config", "external-dir", "add", str(test_dir)])

        # List directories
        result = runner.invoke(app, ["config", "external-dir", "list"])

        assert result.exit_code == 0
        assert "list-test" in result.output

    def test_shows_status_indicator(self, temp_dir: Path):
        """Should show status indicator (✓ or ✗) for existence."""
        # Add a directory that exists
        test_dir = temp_dir / "exists"
        test_dir.mkdir()

        runner.invoke(app, ["config", "external-dir", "add", str(test_dir)])
        result = runner.invoke(app, ["config", "external-dir", "list"])

        assert "✓" in result.output


class TestConfigHelp:
    """Tests for config command help."""

    def test_shows_config_help(self):
        """Should show help for config command."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "Manage configuration settings" in result.output

    def test_shows_external_dir_subcommand(self):
        """Should show external-dir subcommand."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "external-dir" in result.output


class TestExternalDirHelp:
    """Tests for external-dir command help."""

    def test_shows_external_dir_help(self):
        """Should show help for external-dir command."""
        result = runner.invoke(app, ["config", "external-dir", "--help"])

        assert result.exit_code == 0
        assert "Manage external command directories" in result.output

    def test_shows_subcommands(self):
        """Should show add, remove, list subcommands."""
        result = runner.invoke(app, ["config", "external-dir", "--help"])

        assert result.exit_code == 0
        assert "add" in result.output
        assert "remove" in result.output
        assert "list" in result.output

    def test_add_help(self):
        """Should show help for add subcommand."""
        result = runner.invoke(app, ["config", "external-dir", "add", "--help"])

        assert result.exit_code == 0
        assert "Add an external command directory" in result.output

    def test_remove_help(self):
        """Should show help for remove subcommand."""
        result = runner.invoke(app, ["config", "external-dir", "remove", "--help"])

        assert result.exit_code == 0
        assert "Remove an external command directory" in result.output

    def test_list_help(self):
        """Should show help for list subcommand."""
        result = runner.invoke(app, ["config", "external-dir", "list", "--help"])

        assert result.exit_code == 0
        assert "List all registered external command directories" in result.output
