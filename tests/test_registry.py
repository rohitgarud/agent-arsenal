"""Tests for the registry module with external directories."""

from pathlib import Path

from agent_arsenal.registry import CommandRegistry


class TestCommandRegistryInit:
    """Tests for CommandRegistry initialization."""

    def test_accepts_external_dirs_parameter(self, commands_dir: Path):
        """Should accept external_dirs parameter."""
        external = Path("/tmp/external")
        registry = CommandRegistry(commands_dir, [external])
        assert registry.external_dirs == [external]

    def test_defaults_to_empty_external_dirs(self, commands_dir: Path):
        """Should default to empty list for external_dirs."""
        registry = CommandRegistry(commands_dir)
        assert registry.external_dirs == []


class TestScanDirectory:
    """Tests for scan_directory method."""

    def test_scans_builtin_directory(self, commands_dir: Path):
        """Should scan built-in commands directory."""
        registry = CommandRegistry(commands_dir)
        root = registry.scan_directory()

        assert len(root.commands) >= 1
        cmd_names = [c.name for c in root.commands]
        assert "test-cmd" in cmd_names

    def test_returns_empty_group_for_nonexistent_dir(self):
        """Should return empty group for non-existent directory."""
        registry = CommandRegistry(Path("/tmp/nonexistent"))
        root = registry.scan_directory()

        assert root.commands == []
        assert root.subgroups == []

    def test_ignores_hidden_files_and_dirs(self, temp_dir: Path):
        """Should ignore files/dirs starting with underscore or dot."""
        commands = temp_dir / "commands"
        commands.mkdir()
        (commands / "visible.md").write_text("---")
        (commands / "_hidden.md").write_text("---")
        (commands / ".dotfile.md").write_text("---")
        (commands / "_hidden").mkdir()

        registry = CommandRegistry(commands)
        root = registry.scan_directory()

        cmd_names = [c.name for c in root.commands]
        assert "visible" in cmd_names
        assert "hidden" not in cmd_names
        assert "dotfile" not in cmd_names


class TestScanAll:
    """Tests for scan_all method (with external directories)."""

    def test_scans_builtin_commands(self, commands_dir: Path):
        """Should scan built-in commands directory."""
        registry = CommandRegistry(commands_dir)
        root = registry.scan_all()

        cmd_names = [c.name for c in root.commands]
        assert "test-cmd" in cmd_names

    def test_scans_external_directories(
        self, commands_dir: Path, external_commands_dir: Path
    ):
        """Should scan external directories."""
        registry = CommandRegistry(commands_dir, [external_commands_dir])
        root = registry.scan_all()

        cmd_names = [c.name for c in root.commands]
        assert "external-cmd" in cmd_names

    def test_builtin_takes_precedence(
        self, commands_dir: Path, temp_dir: Path
    ):
        """Built-in commands should take precedence over external."""
        # Create builtin command
        (commands_dir / "same-name.md").write_text("""---
name: same-name
description: builtin
---
Builtin""")

        # Create external command with same name
        external = temp_dir / "external"
        external.mkdir()
        (external / "same-name.md").write_text("""---
name: same-name
description: external
---
External""")

        registry = CommandRegistry(commands_dir, [external])
        root = registry.scan_all()

        # Should have only one command (builtin)
        same_name_cmds = [c for c in root.commands if c.name == "same-name"]
        assert len(same_name_cmds) == 1
        # Built-in takes precedence - path should be from commands directory
        assert "commands" in str(same_name_cmds[0].path)

    def test_skips_nonexistent_external_dir(
        self, commands_dir: Path, temp_dir: Path
    ):
        """Should handle non-existent external directories gracefully."""
        nonexistent = temp_dir / "does-not-exist"
        registry = CommandRegistry(commands_dir, [nonexistent])

        # Should not raise
        root = registry.scan_all()

        # Built-in command should still be present
        cmd_names = [c.name for c in root.commands]
        assert "test-cmd" in cmd_names

    def test_scans_external_subdirectories(
        self, commands_dir: Path, temp_dir: Path
    ):
        """Should scan external directories recursively."""
        external = temp_dir / "external"
        external.mkdir()
        (external / "subdir").mkdir()
        (external / "subdir" / "nested-cmd.md").write_text("""---
name: nested-cmd
---
Nested""")
        (external / "top-cmd.md").write_text("""---
name: top-cmd
---
Top""")

        registry = CommandRegistry(commands_dir, [external])
        root = registry.scan_all()

        cmd_names = [c.name for c in root.commands]
        assert "nested-cmd" in cmd_names
        assert "top-cmd" in cmd_names


class TestGetCommand:
    """Tests for get_command method."""

    def test_finds_builtin_command(self, commands_dir: Path):
        """Should find commands by name."""
        registry = CommandRegistry(commands_dir)
        registry.scan_all()

        cmd = registry.get_command("root.test-cmd")
        assert cmd is not None
        assert cmd.name == "test-cmd"

    def test_finds_external_command(
        self, commands_dir: Path, external_commands_dir: Path
    ):
        """Should find external commands."""
        registry = CommandRegistry(commands_dir, [external_commands_dir])
        registry.scan_all()

        cmd = registry.get_command("external.external-cmd")
        assert cmd is not None
        assert cmd.name == "external-cmd"

    def test_returns_none_for_unknown_command(self, commands_dir: Path):
        """Should return None for unknown commands."""
        registry = CommandRegistry(commands_dir)
        registry.scan_all()

        cmd = registry.get_command("nonexistent")
        assert cmd is None


class TestExternalDirectoryScanning:
    """Tests for external directory scanning behavior."""

    def test_multiple_external_dirs_scanned_in_order(
        self, commands_dir: Path, temp_dir: Path
    ):
        """Should scan external directories in order."""
        ext1 = temp_dir / "ext1"
        ext1.mkdir()
        (ext1 / "cmd1.md").write_text("""---
name: cmd1
---
Ext1""")

        ext2 = temp_dir / "ext2"
        ext2.mkdir()
        (ext2 / "cmd2.md").write_text("""---
name: cmd2
---
Ext2""")

        registry = CommandRegistry(commands_dir, [ext1, ext2])
        root = registry.scan_all()

        cmd_names = [c.name for c in root.commands]
        assert "cmd1" in cmd_names
        assert "cmd2" in cmd_names

    def test_empty_external_dirs_list(self, commands_dir: Path):
        """Should work with empty external_dirs list."""
        registry = CommandRegistry(commands_dir, [])
        root = registry.scan_all()

        cmd_names = [c.name for c in root.commands]
        assert "test-cmd" in cmd_names
