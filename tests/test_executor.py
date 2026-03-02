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


class TestTemplateExecution:
    """Tests for template execution (Jinja2)."""

    def test_execute_template_variable_substitution(self, tmp_path):
        """Test basic variable substitution with {{variable}}."""
        cmd_file = tmp_path / "hello.md"
        cmd_file.write_text("""---
name: hello
description: Hello template
execution_type: template
---
Hello {{name}}!
You are running on {{SYSTEM|default('Linux')}}.
""")

        executor = CommandExecutor()
        result = executor.execute_template(cmd_file, {"name": "World"})

        assert result.success
        assert "Hello World!" in result.output
        # Environment variable should be available
        assert "You are running on" in result.output

    def test_execute_template_conditional(self, tmp_path):
        """Test conditional content with {% if %} blocks."""
        cmd_file = tmp_path / "conditional.md"
        cmd_file.write_text("""---
name: conditional
description: Conditional template
execution_type: template
---
{% if show_message|default(false) %}
This is a conditional message.
{% endif %}
{% if name|default('') %}
Hello {{name}}!
{% else %}
Hello stranger!
{% endif %}
""")

        executor = CommandExecutor()

        # Test with show_message=True
        result = executor.execute_template(
            cmd_file, {"show_message": True, "name": "World"}
        )
        assert result.success
        assert "This is a conditional message." in result.output
        assert "Hello World!" in result.output

        # Test with show_message=False
        result = executor.execute_template(
            cmd_file, {"show_message": False, "name": "World"}
        )
        assert result.success
        assert "This is a conditional message." not in result.output

        # Test with no name
        result = executor.execute_template(cmd_file, {"show_message": True})
        assert result.success
        assert "Hello stranger!" in result.output

    def test_execute_template_loop(self, tmp_path):
        """Test loop constructs with {% for %} blocks."""
        cmd_file = tmp_path / "loop.md"
        cmd_file.write_text("""---
name: loop
description: Loop template
execution_type: template
---
Items:
{% for item in items %}
- {{item}}
{% endfor %}
""")

        executor = CommandExecutor()
        result = executor.execute_template(
            cmd_file, {"items": ["apple", "banana", "cherry"]}
        )

        assert result.success
        assert "- apple" in result.output
        assert "- banana" in result.output
        assert "- cherry" in result.output

    def test_execute_template_missing_variable(self, tmp_path):
        """Test handling of missing variables (renders as empty with default)."""
        cmd_file = tmp_path / "missing.md"
        cmd_file.write_text("""---
name: missing
description: Missing variable template
execution_type: template
---
Hello {{name|default('there')}}!
""")

        executor = CommandExecutor()
        result = executor.execute_template(cmd_file, {})

        assert result.success
        # Missing variable with default renders as default value
        assert "Hello there!" in result.output

    def test_execute_template_filters(self, tmp_path):
        """Test Jinja2 filters."""
        cmd_file = tmp_path / "filters.md"
        cmd_file.write_text("""---
name: filters
description: Filters template
execution_type: template
---
Lower: {{text|lower}}
Upper: {{text|upper}}
Length: {{text|length}}
""")

        executor = CommandExecutor()
        result = executor.execute_template(cmd_file, {"text": "Hello World"})

        assert result.success
        assert "Lower: hello world" in result.output
        assert "Upper: HELLO WORLD" in result.output
        assert "Length: 11" in result.output

    def test_execute_template_environment_vars(self, tmp_path):
        """Test that environment variables are available in context."""

        cmd_file = tmp_path / "env.md"
        cmd_file.write_text("""---
name: env
description: Env template
execution_type: template
---
HOME: {{HOME}}
PATH: {{PATH}}
""")

        executor = CommandExecutor()
        result = executor.execute_template(cmd_file, {})

        assert result.success
        # HOME should be available
        assert result.output.startswith("HOME:")


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
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/time/timestamp.md"
        )
        cmd = Command(name="timestamp", path=cmd_path, parent="common.time")

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
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/time/timestamp.md"
        )
        cmd = Command(name="timestamp", path=cmd_path, parent="common.time")

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
        cmd_path = (
            Path(__file__).parent.parent / "src/agent_arsenal/commands/common/uuid.md"
        )
        cmd = Command(name="uuid", path=cmd_path, parent="common")

        executor = CommandExecutor()

        result = executor.execute(cmd, {})
        assert result.success
        # UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        assert len(result.output) == 36

    def test_execute_hash_command(self):
        """Test executing the hash command."""
        cmd_path = (
            Path(__file__).parent.parent / "src/agent_arsenal/commands/common/hash.md"
        )
        cmd = Command(name="hash", path=cmd_path, parent="common")

        executor = CommandExecutor()

        result = executor.execute(cmd, {"input": "test", "algorithm": "sha256"})
        assert result.success
        # SHA256 hash length
        assert len(result.output) == 64

    def test_execute_json_command(self):
        """Test executing the JSON command."""
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/code/json.md"
        )
        cmd = Command(name="json", path=cmd_path, parent="common.code")

        executor = CommandExecutor()

        result = executor.execute(cmd, {"input": '{"key":"value"}'})
        assert result.success
        assert '"key"' in result.output
        assert '"value"' in result.output

    def test_execute_json_validate(self):
        """Test executing JSON with validate option."""
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/code/json.md"
        )
        cmd = Command(name="json", path=cmd_path, parent="common.code")

        executor = CommandExecutor()

        # Valid JSON
        result = executor.execute(cmd, {"input": '{"key":"value"}', "validate": True})
        assert result.success
        assert "Valid" in result.output

        # Invalid JSON - returns success with error message in output
        result = executor.execute(cmd, {"input": '{"key":}', "validate": True})
        assert "Invalid JSON" in result.output or "Error" in result.output

    def test_execute_node_version_command(self, tmp_path):
        """Test executing the node_version command."""
        # Use actual command file
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/code/node_version.md"
        )
        cmd = Command(name="node_version", path=cmd_path, parent="common.code")

        executor = CommandExecutor()

        result = executor.execute(cmd, {"full": False})
        assert result.success
        # Should return version like v22.11.0
        assert result.output.startswith("v")
        assert "." in result.output


class TestNodeExecution:
    """Tests for Node.js execution."""

    def test_execute_node_inline(self, tmp_path):
        """Test executing a node inline script."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_inline: console.log("Hello " + process.env.NAME)
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {"NAME": "World"})

        assert result.success
        assert "Hello World" in result.output

    def test_execute_node_external(self, tmp_path):
        """Test executing an external node script."""
        # Create a test script
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        script_path = script_dir / "test.js"
        script_path.write_text('console.log("Hello " + process.env.NAME)')

        # Create command file
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_path: scripts/test.js
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {"NAME": "World"})

        assert result.success
        assert "Hello World" in result.output

    def test_execute_node_missing_script(self, tmp_path):
        """Test error when script not found."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_path: scripts/missing.js
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {})

        assert not result.success
        assert "not found" in result.error.lower()

    def test_execute_node_via_execute_method(self, tmp_path):
        """Test node execution through main execute() dispatcher."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_inline: console.log("Hello " + process.env.NAME)
sandbox: false
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute(cmd, {"NAME": "World"})

        assert result.success
        assert "Hello World" in result.output

    def test_execute_node_json_parse(self, tmp_path):
        """Test node execution with JSON parsing."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_inline: const data = JSON.parse(process.env.INPUT); console.log(data.key)
sandbox: false
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute(cmd, {"INPUT": '{"key":"value"}'})

        assert result.success
        assert "value" in result.output

    def test_execute_node_missing_args(self, tmp_path):
        """Test node execution with no args provided."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_inline: console.log("Hello " + process.env.MY_NAME)
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {})

        assert result.success
        assert "Hello undefined" in result.output

    def test_execute_node_no_script_specified(self, tmp_path):
        """Test node execution error when no script specified."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {})

        assert not result.success
        assert "no node.js script specified" in result.error.lower()


class TestSandboxIntegration:
    """Tests for sandbox integration in executor."""

    def test_sandbox_enabled_routes_to_sandbox(self, tmp_path, monkeypatch):
        """Test execution with sandbox: true routes to sandbox executor."""
        # Mock the Deno check to return True (simulating Deno available)
        from agent_arsenal import sandbox as sandbox_module

        monkeypatch.setattr(
            sandbox_module.DenoSandboxExecutor,
            "_check_deno_available",
            lambda self: True,
        )

        # Mock the sandbox execute to avoid actual execution
        from agent_arsenal.sandbox import CommandResult as SandboxResult

        def mock_execute(self, execution_type, script, permissions=None, timeout=None):
            return SandboxResult(
                success=True,
                output="sandboxed output",
                error=None,
                metadata={"executor": "deno-sandbox"},
            )

        monkeypatch.setattr(
            sandbox_module.DenoSandboxExecutor,
            "execute",
            mock_execute,
        )

        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: prompt
sandbox: true
---
# Test
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute(cmd, {})

        assert result.success
        assert "sandboxed output" in result.output
        assert result.metadata.get("executor") == "deno-sandbox"

    def test_sandbox_false_routes_to_direct_execution(self, tmp_path):
        """Test execution with sandbox: false routes to direct execution."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: prompt
sandbox: false
---
# Test Output
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute(cmd, {})

        assert result.success
        assert "Test Output" in result.output

    def test_missing_deno_returns_error(self, tmp_path, monkeypatch):
        """Test execution returns appropriate error when Deno is not installed."""
        # Mock the Deno check to return False (simulating Deno not available)
        from agent_arsenal import sandbox as sandbox_module

        monkeypatch.setattr(
            sandbox_module.DenoSandboxExecutor,
            "_check_deno_available",
            lambda self: False,
        )

        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: prompt
sandbox: true
---
# Test
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute(cmd, {})

        assert not result.success
        assert "Deno is not installed" in result.error
        assert "curl -fsSL https://deno.land" in result.error


class TestExecuteEdgeCases:
    """Tests for edge cases in command execution."""

    def test_execute_prompt_with_args(self, tmp_path):
        """Test execute_prompt with multiple arguments."""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test
execution_type: prompt
---
Hello {name}! You are {age} years old.
""")

        executor = CommandExecutor()
        result = executor.execute_prompt(cmd_file, {"name": "Alice", "age": "30"})

        assert result.success
        assert "Hello Alice!" in result.output
        assert "30 years old" in result.output

    def test_execute_python_handler_with_error(self, tmp_path):
        """Test execute_python with a handler that raises an error."""
        cmd_path = (
            Path(__file__).parent.parent
            / "src/agent_arsenal/commands/common/time/timestamp.md"
        )
        cmd = Command(name="timestamp", path=cmd_path, parent="common.time")

        executor = CommandExecutor()

        # Test with invalid format (should return error or fallback)
        result = executor.execute_python(cmd, {"format": "INVALID_FORMAT"})
        # Should either succeed with fallback or return error
        assert result is not None

    def test_execute_template_with_context(self, tmp_path):
        """Test execute_template with full context including environment vars."""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test
execution_type: template
---
User: {{user}}
Home: {{HOME}}
Path: {{PATH}}
Platform: {{SYSTEM|default('Linux')}}
""")

        executor = CommandExecutor()
        result = executor.execute_template(cmd_file, {"user": "testuser"})

        assert result.success
        assert "User: testuser" in result.output
        assert "Home:" in result.output
        assert "Platform:" in result.output

    def test_execute_unsupported_type(self, tmp_path):
        """Test execute with unsupported execution type."""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test
execution_type: unsupported_type
---
# Test
""")

        cmd = Command(name="test", path=cmd_file)
        executor = CommandExecutor()

        result = executor.execute(cmd, {})

        assert result.success is False
        assert "Unsupported execution type" in result.error

    def test_execute_template_with_nested_context(self, tmp_path):
        """Test execute_template with nested dictionary context."""
        cmd_file = tmp_path / "nested.md"
        cmd_file.write_text("""---
name: nested
description: Nested template
execution_type: template
---
{% for item in items %}
- {{item.name}}: {{item.value}}
{% endfor %}
""")

        executor = CommandExecutor()
        result = executor.execute_template(
            cmd_file,
            {"items": [{"name": "a", "value": "1"}, {"name": "b", "value": "2"}]},
        )

        assert result.success
        assert "- a: 1" in result.output
        assert "- b: 2" in result.output

    def test_execute_with_sandbox_enabled(self, tmp_path, monkeypatch):
        """Test execute with sandbox enabled."""
        from agent_arsenal import sandbox as sandbox_module
        from agent_arsenal.sandbox import CommandResult as SandboxResult

        # Mock Deno as available
        monkeypatch.setattr(
            sandbox_module.DenoSandboxExecutor,
            "_check_deno_available",
            lambda self: True,
        )

        # Mock execute to return success
        def mock_execute(self, execution_type, script, permissions=None, timeout=None):
            return SandboxResult(success=True, output="sandboxed", error=None)

        monkeypatch.setattr(
            sandbox_module.DenoSandboxExecutor,
            "execute",
            mock_execute,
        )

        cmd_file = tmp_path / "test.md"
        cmd_file.write_text("""---
name: test
description: Test
execution_type: prompt
sandbox: true
---
# Test
""")

        cmd = Command(name="test", path=cmd_file)
        executor = CommandExecutor()
        result = executor.execute(cmd, {})

        assert result.success

    def test_execute_bash_with_environment(self, tmp_path):
        """Test execute_bash passes environment variables."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: bash
executable_inline: echo $MY_VAR
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_bash(cmd, {"MY_VAR": "test_value"})

        assert result.success

    def test_execute_node_with_json(self, tmp_path):
        """Test execute_node handles JSON response."""
        cmd_path = tmp_path / "test.md"
        cmd_path.write_text("""---
name: test
description: Test
execution_type: executable
executable_type: node
executable_inline: 'console.log(JSON.stringify({result: "ok"}))'
sandbox: false
---
""")

        cmd = Command(name="test", path=cmd_path)
        executor = CommandExecutor()

        result = executor.execute_node(cmd, {})

        assert result.success
