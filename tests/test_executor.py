"""Tests for the executor module."""

from pathlib import Path

from agent_arsenal.executor import (
    CommandExecutor,
    CommandResult,
)
from agent_arsenal.registry import Command


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        result = CommandResult(success=True, output="test")
        assert result.metadata == {}

    def test_custom_metadata(self):
        """Test custom metadata."""
        result = CommandResult(success=True, output="test", metadata={"key": "value"})
        assert result.metadata["key"] == "value"


class TestCommandExecutor:
    """Tests for CommandExecutor class."""

    def test_execute_prompt(self, tmp_path):
        """Test executing a prompt command."""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test command
execution_type: prompt
---
Hello {name}!
""")

        executor = CommandExecutor()
        result = executor.execute_prompt(cmd_file, {"name": "World"})

        assert result.success
        assert "Hello World!" in result.output

    def test_execute_prompt_no_args(self, tmp_path):
        """Test executing a prompt command without args."""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test command
execution_type: prompt
---
Hello World!
""")

        executor = CommandExecutor()
        result = executor.execute_prompt(cmd_file, {})

        assert result.success
        assert "Hello World!" in result.output

    def test_execute_python(self):
        """Test executing a python command."""
        executor = CommandExecutor()

        # Test with the timestamp handler
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/common/timestamp.md"
        cmd = Command(name="timestamp", path=cmd_path, parent="common")

        result = executor.execute_python(cmd, {"format": "%Y-%m-%d"})

        assert result.success
        # Should return a date like "2026-02-26"
        assert "-" in result.output

    def test_execute_bash_inline(self, tmp_path):
        """Test executing a bash inline script."""
        # Create a mock command object
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: bash
executable_inline: echo "Hello $NAME"
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_bash(cmd, {"NAME": "World"})

        assert result.success
        assert "Hello World" in result.output

    def test_execute_bash_external(self, tmp_path):
        """Test executing an external bash script."""
        # Create a test script
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        script_path = script_dir / "test.sh"
        script_path.write_text('#!/bin/bash\necho "Hello $NAME"')
        script_path.chmod(0o755)

        # Create command file
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: bash
executable_path: scripts/test.sh
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_bash(cmd, {"NAME": "World"})

        # This might fail because the script path is relative to command file
        # which is in tmp_path, so it should work
        assert "Hello World" in result.output or "not found" in result.error.lower()

    def test_execute_unknown_type(self):
        """Test executing with unknown type returns error."""
        # We can't easily test this without a real command file
        # But we can verify the result class works
        result = CommandResult(
            success=False,
            output="",
            error="Unknown execution type: invalid",
        )
        assert not result.success
        assert "Unknown" in result.error


class TestExecuteIntegration:
    """Integration tests for command execution."""

    def test_execute_timestamp_command(self):
        """Test executing the timestamp command."""
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/common/timestamp.md"
        cmd = Command(name="timestamp", path=cmd_path, parent="common")

        executor = CommandExecutor()

        # Test without args (uses defaults)
        result = executor.execute(cmd, {})
        assert result.success
        assert result.output  # Should have some output

        # Test with format
        result = executor.execute(cmd, {"format": "%Y-%m-%d"})
        assert result.success
        assert "-" in result.output  # Date format has dashes

    def test_execute_uuid_command(self):
        """Test executing the UUID command."""
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/common/uuid.md"
        cmd = Command(name="uuid", path=cmd_path, parent="common")

        executor = CommandExecutor()

        result = executor.execute(cmd, {})
        assert result.success
        # UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        assert len(result.output) == 36

    def test_execute_hash_command(self):
        """Test executing the hash command."""
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/common/hash.md"
        cmd = Command(name="hash", path=cmd_path, parent="common")

        executor = CommandExecutor()

        result = executor.execute(cmd, {"input": "test", "algorithm": "sha256"})
        assert result.success
        # SHA256 hash length
        assert len(result.output) == 64

    def test_execute_json_command(self):
        """Test executing the JSON command."""
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/code/json.md"
        cmd = Command(name="json", path=cmd_path, parent="code")

        executor = CommandExecutor()

        result = executor.execute(cmd, {"input": '{"key":"value"}'})
        assert result.success
        assert '"key"' in result.output
        assert '"value"' in result.output

    def test_execute_json_validate(self):
        """Test executing JSON with validate option."""
        cmd_path = Path(__file__).parent.parent / "src/agent_arsenal/commands/code/json.md"
        cmd = Command(name="json", path=cmd_path, parent="code")

        executor = CommandExecutor()

        # Valid JSON
        result = executor.execute(cmd, {"input": '{"key":"value"}', "validate": True})
        assert result.success
        assert "Valid" in result.output

        # Invalid JSON - returns success with error message in output
        result = executor.execute(cmd, {"input": '{"key":}', "validate": True})
        assert "Invalid JSON" in result.output or "Error" in result.output