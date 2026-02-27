"""Tests for the validator module."""

import pytest
from pydantic import ValidationError

from agent_arsenal.validator import Argument, CommandFrontmatter


class TestNameValidation:
    """Tests for command name validation."""

    def test_valid_name(self):
        """Test valid name passes validation."""
        fm = CommandFrontmatter(
            name="test-command",
            description="A valid test command",
        )
        assert fm.name == "test-command"

    def test_name_must_be_lowercase(self):
        """Test name must be lowercase."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="Test-Command",
                description="A test command",
            )
        assert "lowercase" in str(exc.value).lower()

    def test_name_valid_identifier(self):
        """Test name must be a valid identifier."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test command",
                description="A test command",
            )
        assert "valid identifier" in str(exc.value).lower()

    def test_name_cannot_start_with_number(self):
        """Test name cannot start with a number."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="1test",
                description="A test command",
            )
        assert "valid identifier" in str(exc.value).lower()

    def test_name_cannot_be_python_keyword(self):
        """Test name cannot be a Python keyword."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="class",
                description="A test command",
            )
        assert "keyword" in str(exc.value).lower()

    def test_name_max_length(self):
        """Test name max length is 50 characters."""
        long_name = "a" * 51
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name=long_name,
                description="A test command",
            )
        assert "characters" in str(exc.value).lower()

    def test_name_with_underscore(self):
        """Test name with underscore is valid."""
        fm = CommandFrontmatter(
            name="test_command",
            description="A valid test command",
        )
        assert fm.name == "test_command"


class TestVersionValidation:
    """Tests for version validation."""

    def test_valid_version(self):
        """Test valid semver passes."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            version="1.0.0",
        )
        assert fm.version == "1.0.0"

    def test_version_with_patch(self):
        """Test version with patch number."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            version="1.2.3",
        )
        assert fm.version == "1.2.3"

    def test_version_prerelease(self):
        """Test version with prerelease."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            version="1.0.0-alpha",
        )
        assert fm.version == "1.0.0-alpha"

    def test_version_build_metadata(self):
        """Test version with build metadata."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            version="1.0.0+build",
        )
        assert fm.version == "1.0.0+build"

    def test_invalid_version(self):
        """Test invalid version format fails."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                version="1.0",
            )
        assert "version" in str(exc.value).lower()

    def test_invalid_version_letters(self):
        """Test version with letters fails."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                version="1.0.a",
            )
        assert "version" in str(exc.value).lower()


class TestDescriptionValidation:
    """Tests for description validation."""

    def test_valid_description(self):
        """Test valid description passes."""
        fm = CommandFrontmatter(
            name="test",
            description="A valid test command description",
        )
        assert fm.description == "A valid test command description"

    def test_description_min_length(self):
        """Test description min length is 10."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="short",
            )
        assert "description" in str(exc.value).lower()

    def test_description_max_length(self):
        """Test description max length is 200."""
        long_desc = "a" * 201
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description=long_desc,
            )
        assert "description" in str(exc.value).lower()


class TestArgumentValidation:
    """Tests for argument validation."""

    def test_valid_argument(self):
        """Test valid argument passes."""
        arg = Argument(
            name="input",
            type="string",
            description="Input string",
        )
        assert arg.name == "input"

    def test_argument_name_valid_identifier(self):
        """Test argument name must be valid identifier."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="invalid name",
                type="string",
                description="Input string",
            )
        assert "valid identifier" in str(exc.value).lower()

    def test_argument_name_cannot_start_with_number(self):
        """Test argument name cannot start with number."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="1input",
                type="string",
                description="Input string",
            )
        assert "valid identifier" in str(exc.value).lower()

    def test_required_argument_no_default(self):
        """Test required argument cannot have default value."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="input",
                type="string",
                description="Input string",
                required=True,
                default="some_value",
            )
        assert "required" in str(exc.value).lower()

    def test_default_type_mismatch_string(self):
        """Test default value type mismatch for string."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="input",
                type="string",
                description="Input string",
                default=123,
            )
        assert "type mismatch" in str(exc.value).lower()

    def test_default_type_mismatch_int(self):
        """Test default value type mismatch for int."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="count",
                type="int",
                description="Count value",
                default="not an int",
            )
        assert "type mismatch" in str(exc.value).lower()

    def test_default_type_mismatch_bool(self):
        """Test default value type mismatch for bool."""
        with pytest.raises(ValidationError) as exc:
            Argument(
                name="verbose",
                type="bool",
                description="Verbose flag",
                default="true",
            )
        assert "type mismatch" in str(exc.value).lower()

    def test_valid_argument_with_default(self):
        """Test valid argument with default value."""
        arg = Argument(
            name="input",
            type="string",
            description="Input string",
            default="",
        )
        assert arg.default == ""

    def test_valid_boolean_type(self):
        """Test boolean type is accepted."""
        arg = Argument(
            name="verbose",
            type="bool",
            description="Verbose flag",
            default=False,
        )
        assert arg.type == "bool"

    def test_valid_boolean_type_alias(self):
        """Test 'boolean' type alias is accepted (from real commands)."""
        arg = Argument(
            name="verbose",
            type="boolean",
            description="Verbose flag",
            default=False,
        )
        assert arg.type == "boolean"

    def test_valid_integer_type(self):
        """Test integer type is accepted."""
        arg = Argument(
            name="count",
            type="int",
            description="Count value",
            default=1,
        )
        assert arg.type == "int"

    def test_valid_integer_type_alias(self):
        """Test 'integer' type alias is accepted (from real commands)."""
        arg = Argument(
            name="count",
            type="integer",
            description="Count value",
            default=1,
        )
        assert arg.type == "integer"


class TestUniqueArgumentNames:
    """Tests for unique argument names validation."""

    def test_unique_argument_names(self):
        """Test unique argument names pass."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            args=[
                Argument(name="input", type="string", description="Input"),
                Argument(name="output", type="string", description="Output"),
            ],
        )
        assert len(fm.args) == 2

    def test_duplicate_argument_names(self):
        """Test duplicate argument names fail."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                args=[
                    Argument(name="input", type="string", description="Input"),
                    Argument(name="input", type="string", description="Input"),
                ],
            )
        assert "duplicate" in str(exc.value).lower()


class TestInlineTypeValidation:
    """Tests for inline executable type validation."""

    def test_inline_type_matches_executable_type(self):
        """Test executable_inline_type must match executable_type."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            execution_type="executable",
            executable_type="bash",
            executable_inline="echo hello",
            executable_inline_type="bash",
        )
        assert fm.executable_inline_type == "bash"

    def test_inline_type_mismatch_fails(self):
        """Test inline type mismatch fails."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                execution_type="executable",
                executable_type="bash",
                executable_inline="echo hello",
                executable_inline_type="node",
            )
        assert "match" in str(exc.value).lower()


class TestAliasesValidation:
    """Tests for aliases validation."""

    def test_valid_aliases(self):
        """Test valid aliases pass."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            aliases=["test-cmd", "tcmd"],
        )
        assert fm.aliases == ["test-cmd", "tcmd"]

    def test_aliases_must_be_lowercase(self):
        """Test aliases must be lowercase."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="my-cmd",
                description="A test command",
                aliases=["MYCMD"],
            )
        assert "lowercase" in str(exc.value).lower()

    def test_aliases_must_be_unique(self):
        """Test aliases must be unique."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                aliases=["test", "test"],
            )
        assert "unique" in str(exc.value).lower()

    def test_aliases_cannot_contain_name(self):
        """Test aliases cannot contain command name."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                aliases=["test"],
            )
        assert "command name" in str(exc.value).lower()


class TestTagsValidation:
    """Tests for tags validation."""

    def test_valid_tags(self):
        """Test valid tags pass."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            tags=["utility", "format"],
        )
        assert fm.tags == ["utility", "format"]

    def test_tags_must_be_lowercase(self):
        """Test tags must be lowercase."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                tags=["UTILITY"],
            )
        assert "lowercase" in str(exc.value).lower()

    def test_tags_must_be_unique(self):
        """Test tags must be unique."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                tags=["utility", "utility"],
            )
        assert "unique" in str(exc.value).lower()


class TestReturnsValidation:
    """Tests for returns validation."""

    def test_valid_returns(self):
        """Test valid returns pass."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            returns={"type": "string", "description": "Output string"},
        )
        assert fm.returns == {"type": "string", "description": "Output string"}

    def test_returns_requires_type(self):
        """Test returns must have type field."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                returns={"description": "Output"},
            )
        assert "type" in str(exc.value).lower()

    def test_returns_invalid_type(self):
        """Test returns type must be valid."""
        with pytest.raises(ValidationError) as exc:
            CommandFrontmatter(
                name="test",
                description="A test command",
                returns={"type": "invalid"},
            )
        assert "type" in str(exc.value).lower()


class TestCategoryValidation:
    """Tests for category validation."""

    def test_valid_category(self):
        """Test valid category passes."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
            category="database",
        )
        assert fm.category == "database"

    def test_category_is_optional(self):
        """Test category is optional."""
        fm = CommandFrontmatter(
            name="test",
            description="A test command",
        )
        assert fm.category is None
