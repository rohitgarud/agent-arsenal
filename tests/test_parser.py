"""Tests for the parser module."""

import pytest
from pathlib import Path

from agent_arsenal.parser import (
    parse_markdown_command,
    split_frontmatter,
    validate_frontmatter,
    get_handler_info,
    ValidationError,
)


class TestSplitFrontmatter:
    """Tests for split_frontmatter function."""

    def test_split_valid_frontmatter(self):
        """Test splitting valid frontmatter."""
        content = """---
name: test
description: Test command
---
# Body content
"""
        fm, body = split_frontmatter(content)
        assert "name: test" in fm
        assert "# Body content" in body

    def test_split_no_frontmatter(self):
        """Test splitting content without frontmatter."""
        content = "# Just body content"
        fm, body = split_frontmatter(content)
        assert fm == ""
        assert body == content


class TestParseMarkdownCommand:
    """Tests for parse_markdown_command function."""

    def test_parse_valid_command(self, tmp_path):
        """Test parsing a valid command file."""
        content = """---
name: test
description: Test command
execution_type: prompt
---
# Body
"""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text(content)

        fm, body = parse_markdown_command(cmd_file)
        assert fm["name"] == "test"
        assert fm["description"] == "Test command"
        assert fm["execution_type"] == "prompt"
        assert "# Body" in body

    def test_parse_missing_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_markdown_command(Path("/nonexistent/test.md"))

    def test_normalize_field_names(self, tmp_path):
        """Test normalization of old field names to new format."""
        content = """---
name: test
description: Test command
execution_type: python
python_function: timestamp.handle_timestamp
---
# Body
"""
        cmd_file = tmp_path / "test.md"
        cmd_file.write_text(content)

        fm, _ = parse_markdown_command(cmd_file)

        # Should be normalized to new format
        assert fm["execution_type"] == "executable"
        assert fm["executable_type"] == "python"
        assert fm["executable_path"] == "timestamp.handle_timestamp"


class TestValidateFrontmatter:
    """Tests for validate_frontmatter function."""

    def test_valid_prompt_command(self):
        """Test validation of valid prompt command."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "prompt",
        }
        result = validate_frontmatter(fm)
        assert result["name"] == "test"

    def test_valid_executable_command_python(self):
        """Test validation of valid executable (python) command."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "executable",
            "executable_type": "python",
            "executable_path": "handlers.test",
        }
        result = validate_frontmatter(fm)
        assert result["executable_path"] == "handlers.test"

    def test_missing_name(self):
        """Test validation fails with missing name."""
        fm = {
            "description": "Test command",
            "execution_type": "prompt",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "name" in str(exc.value).lower()

    def test_missing_description(self):
        """Test validation fails with missing description."""
        fm = {
            "name": "test",
            "execution_type": "prompt",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "description" in str(exc.value).lower()

    def test_invalid_execution_type(self):
        """Test validation fails with invalid execution type."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "invalid",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "execution_type" in str(exc.value).lower()

    def test_executable_requires_type(self):
        """Test validation fails when executable missing type."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "executable",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "executable_type" in str(exc.value).lower()

    def test_python_requires_path(self):
        """Test validation fails when python missing path."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "executable",
            "executable_type": "python",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "executable_path" in str(exc.value).lower()

    def test_bash_requires_path_or_inline(self):
        """Test validation fails when bash missing path and inline."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "executable",
            "executable_type": "bash",
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert (
            "executable_path" in str(exc.value).lower()
            or "inline" in str(exc.value).lower()
        )

    def test_valid_args(self):
        """Test validation of valid args."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "prompt",
            "args": [
                {"name": "format", "type": "string", "default": "%Y-%m-%d"},
                {"name": "count", "type": "integer", "default": 1},
                {"name": "verbose", "type": "boolean", "default": False},
            ],
        }
        result = validate_frontmatter(fm)
        assert len(result["args"]) == 3

    def test_invalid_arg_type(self):
        """Test validation fails with invalid arg type."""
        fm = {
            "name": "test",
            "description": "Test command",
            "execution_type": "prompt",
            "args": [
                {"name": "test", "type": "invalid"},
            ],
        }
        with pytest.raises(ValidationError) as exc:
            validate_frontmatter(fm)
        assert "type" in str(exc.value).lower()


class TestGetHandlerInfo:
    """Tests for get_handler_info function."""

    def test_prompt_handler(self):
        """Test getting handler info for prompt type."""
        fm = {
            "name": "test",
            "description": "Test",
            "execution_type": "prompt",
        }
        info = get_handler_info(fm)
        assert info["type"] == "prompt"

    def test_python_handler(self):
        """Test getting handler info for python type."""
        fm = {
            "name": "test",
            "description": "Test",
            "execution_type": "executable",
            "executable_type": "python",
            "executable_path": "handlers.test",
        }
        info = get_handler_info(fm)
        assert info["type"] == "python"
        assert info["path"] == "handlers.test"

    def test_bash_handler(self):
        """Test getting handler info for bash type."""
        fm = {
            "name": "test",
            "description": "Test",
            "execution_type": "executable",
            "executable_type": "bash",
            "executable_path": "scripts/test.sh",
            "executable_inline": "echo hello",
        }
        info = get_handler_info(fm)
        assert info["type"] == "bash"
        assert info["path"] == "scripts/test.sh"
        assert info["inline"] == "echo hello"
