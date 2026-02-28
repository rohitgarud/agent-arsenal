"""Pydantic models for command validation."""

import keyword
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Executable types that require executable_path only (no inline option)
_EXECUTABLE_PATH_REQUIRED: tuple[str, ...] = ("python",)
# Executable types that require either executable_path or executable_inline
_EXECUTABLE_PATH_OR_INLINE: tuple[str, ...] = ("bash", "node", "typescript")

# Valid argument types (includes both Python names and common YAML aliases)
_VALID_ARG_TYPES = {
    "string",
    "int",
    "integer",
    "float",
    "bool",
    "boolean",
    "list",
    "dict",
}

# Type mapping for default value validation
_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "int": int,
    "integer": int,
    "float": (int, float),
    "bool": bool,
    "boolean": bool,
    "list": list,
    "dict": dict,
}


class Argument(BaseModel):
    """Command argument specification."""

    name: str
    type: str = "string"
    description: str
    required: bool = False
    default: Any | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate argument name."""
        if not v:
            raise ValueError("argument name cannot be empty")
        if not re.match(r"^[a-z_][a-z0-9_]*$", v):
            raise ValueError(
                f"argument name '{v}' must be a valid identifier (lowercase alphanumeric, underscore)"
            )
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate argument type."""
        if v not in _VALID_ARG_TYPES:
            raise ValueError(f"Type must be one of {sorted(_VALID_ARG_TYPES)}")
        return v

    @model_validator(mode="after")
    def validate_required_no_default(self) -> "Argument":
        """Required arguments should not have default values."""
        if self.required and self.default is not None:
            raise ValueError("required argument cannot have a default value")
        return self

    @model_validator(mode="after")
    def validate_default_type(self) -> "Argument":
        """Default value must match declared type."""
        if self.default is None:
            return self

        expected_type = _TYPE_MAP.get(self.type)
        if expected_type and not isinstance(self.default, expected_type):
            raise ValueError(
                f"default value type mismatch: expected {self.type}, "
                f"got {type(self.default).__name__}"
            )
        return self


class CommandFrontmatter(BaseModel):
    """Schema for command frontmatter validation."""

    # Required fields
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=10, max_length=200)
    version: str = "1.0.0"

    # Execution configuration
    execution_type: Literal["prompt", "executable", "template"] = "prompt"
    executable_type: Literal["python", "bash", "node", "typescript"] = "python"
    executable_path: str | None = None
    executable_inline: str | None = None
    executable_inline_type: Literal["bash", "node", "typescript"] | None = None
    # Arguments
    args: list[Argument] = Field(default_factory=list)

    # Optional metadata
    category: str | None = None
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    requires_context: list[str] = Field(default_factory=list)
    returns: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate command name."""
        # Check lowercase
        if v != v.lower():
            raise ValueError("name must be lowercase")

        # Check valid identifier pattern
        if not re.match(r"^[a-z][a-z0-9_-]*$", v):
            raise ValueError(
                "name must be a valid identifier (lowercase alphanumeric, hyphen, underscore)"
            )

        # Check not a keyword
        if keyword.iskeyword(v):
            raise ValueError(f"name '{v}' cannot be a Python keyword")

        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        # Basic semver: X.Y.Z with optional prerelease and build metadata
        semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$"
        if not re.match(semver_pattern, v):
            raise ValueError("version must follow semantic versioning (X.Y.Z)")
        return v

    @field_validator("aliases", mode="before")
    @classmethod
    def validate_aliases(cls, v):
        """Validate aliases field."""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("aliases must be a list")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags field."""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("tags must be a list")
        return v

    @field_validator("executable_path")
    @classmethod
    def validate_executable_path(
        cls, executable_path: str | None, info: Any
    ) -> str | None:
        """Require executable_path when execution_type is executable and executable_type is python."""
        execution_type = info.data.get("execution_type")
        executable_type = info.data.get("executable_type")
        if (
            execution_type == "executable"
            and executable_type in _EXECUTABLE_PATH_REQUIRED
            and not (executable_path and executable_path.strip())
        ):
            raise ValueError(
                f"executable_path required for execution_type={execution_type} "
                f"when executable_type={executable_type}"
            )
        return executable_path

    @model_validator(mode="after")
    def validate_unique_arg_names(self) -> "CommandFrontmatter":
        """All argument names must be unique."""
        names = [arg.name for arg in self.args]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"duplicate argument names: {set(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_executable_path_or_inline(self) -> "CommandFrontmatter":
        """For bash/node/typescript, require either executable_path or executable_inline."""
        if self.execution_type != "executable":
            return self
        if self.executable_type not in _EXECUTABLE_PATH_OR_INLINE:
            return self
        has_path = bool(self.executable_path and self.executable_path.strip())
        has_inline = bool(self.executable_inline and self.executable_inline.strip())
        if not has_path and not has_inline:
            raise ValueError(
                f"executable_type '{self.executable_type}' requires either "
                "'executable_path' or 'executable_inline'"
            )
        # If executable_inline_type is not set but executable_inline is set,
        # we can infer it from executable_type (no need to raise an error)
        return self

    @model_validator(mode="after")
    def validate_inline_type_matches(self) -> "CommandFrontmatter":
        """executable_inline_type must match executable_type when explicitly set."""
        if self.executable_inline and self.executable_inline_type:
            if self.executable_type != self.executable_inline_type:
                raise ValueError(
                    f"executable_inline_type '{self.executable_inline_type}' "
                    f"must match executable_type '{self.executable_type}'"
                )
        return self

    @model_validator(mode="after")
    def validate_aliases_unique(self) -> "CommandFrontmatter":
        """Aliases must be unique and not duplicate name."""
        if not self.aliases:
            return self

        aliases = [a.lower() for a in self.aliases]
        if len(aliases) != len(set(aliases)):
            raise ValueError("aliases must be unique")

        if self.name.lower() in aliases:
            raise ValueError("aliases cannot contain the command name")

        for alias in self.aliases:
            if alias != alias.lower():
                raise ValueError(f"alias '{alias}' must be lowercase")

        return self

    @model_validator(mode="after")
    def validate_tags_format(self) -> "CommandFrontmatter":
        """Tags must be lowercase and unique."""
        if not self.tags:
            return self

        tags = [t.lower() for t in self.tags]
        if len(tags) != len(set(tags)):
            raise ValueError("tags must be unique")

        for tag in self.tags:
            if tag != tag.lower():
                raise ValueError(f"tag '{tag}' must be lowercase")

        return self

    @model_validator(mode="after")
    def validate_returns(self) -> "CommandFrontmatter":
        """Validate returns field structure."""
        if self.returns is None:
            return self

        if not isinstance(self.returns, dict):
            raise ValueError("returns must be a dictionary")

        if "type" not in self.returns:
            raise ValueError("returns must have a 'type' field")

        valid_types = ["string", "int", "float", "bool", "list", "dict", "void"]
        returns_type = self.returns.get("type")
        if returns_type not in valid_types:
            raise ValueError(f"returns type must be one of {valid_types}")

        return self


class GroupFrontmatter(BaseModel):
    """Schema for group info.md frontmatter validation."""

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    order: int | None = None  # Optional ordering for display
