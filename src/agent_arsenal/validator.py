"""Pydantic models for command validation."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class Argument(BaseModel):
    """Command argument specification."""

    name: str
    type: str = "string"
    description: str
    required: bool = False
    default: Optional[Any] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """Validate argument type."""
        allowed_types = ["string", "int", "float", "bool", "list", "dict"]
        if v not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v


class CommandFrontmatter(BaseModel):
    """Schema for command frontmatter validation."""

    # Required fields
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    version: str = "1.0.0"

    # Execution configuration
    execution_type: Literal["prompt", "python", "hybrid", "template"] = "prompt"
    python_function: Optional[str] = None

    # Arguments
    args: List[Argument] = Field(default_factory=list)

    # Optional metadata
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    requires_context: List[str] = Field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None

    @field_validator("python_function")
    @classmethod
    def validate_python_function(cls, v, info):
        """Ensure python_function is provided for python/hybrid execution types."""
        execution_type = info.data.get("execution_type")
        if execution_type in ["python", "hybrid"] and not v:
            raise ValueError(
                f"python_function required for execution_type={execution_type}"
            )
        return v


class GroupFrontmatter(BaseModel):
    """Schema for group info.md frontmatter validation."""

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    order: Optional[int] = None  # Optional ordering for display
