"""Parser for markdown command files with YAML frontmatter."""

import re
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError as YAMLError

from agent_arsenal.exceptions import ValidationError


def parse_markdown_command(file_path: Path) -> tuple[dict[str, Any], str]:
    """Parse a .md command file into frontmatter and body.

    Args:
        file_path: Path to the .md file

    Returns:
        Tuple of (frontmatter_dict, markdown_body)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Command file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    frontmatter_str, body = split_frontmatter(content)

    try:
        frontmatter = (
            yaml.safe_load(frontmatter_str) if frontmatter_str else {}
        )
    except YAMLError as e:
        raise ValueError(f"Error parsing frontmatter in {file_path}: {e}")

    # Normalize field names to support both old and new formats
    frontmatter = _normalize_field_names(frontmatter)

    return frontmatter or {}, body


def _normalize_field_names(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Normalize command field names for backward compatibility.

    This function handles legacy field names that have been renamed,
    allowing old command files to continue working while supporting
    the new field naming convention.

    Field transformations:
        - 'execution_type': 'python' -> 'execution_type': 'executable'
                          with 'executable_type': 'python'
        - 'python_function' -> 'executable_path' (for python executables)

    Old format (deprecated but supported):
        ```yaml
        name: my-command
        execution_type: python
        python_function: handlers.my_module.handle_func
        ```

    New format (current):
        ```yaml
        name: my-command
        execution_type: executable
        executable_type: python
        executable_path: handlers.my_module.handle_func
        ```

    Args:
        frontmatter: The parsed frontmatter dictionary

    Returns:
        Normalized frontmatter with legacy field names converted to new format
    """
    if not frontmatter:
        return frontmatter

    normalized = frontmatter.copy()

    # Handle execution_type normalization
    exec_type = normalized.get("execution_type", "")

    # If using "python" as execution_type, convert to "executable" with python type
    if exec_type == "python":
        normalized["execution_type"] = "executable"
        normalized["executable_type"] = "python"
        # Move python_function to executable_path
        if "python_function" in normalized:
            normalized["executable_path"] = normalized.pop("python_function")

    return normalized


def split_frontmatter(content: str) -> tuple[str, str]:
    """Split content into frontmatter and body.

    Args:
        content: Full markdown content

    Returns:
        Tuple of (frontmatter_yaml, body_markdown)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1), match.group(2)
    return "", content


def validate_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Validate frontmatter against schema.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Validated frontmatter

    Raises:
        ValidationError: If frontmatter is invalid
    """
    errors: list[str] = []

    # Check required fields
    if not frontmatter.get("name"):
        errors.append("Missing required field: 'name'")

    if not frontmatter.get("description"):
        errors.append("Missing required field: 'description'")

    # Validate execution_type
    execution_type = frontmatter.get("execution_type", "prompt")
    valid_execution_types = ["prompt", "executable", "template"]

    if execution_type not in valid_execution_types:
        errors.append(
            f"Invalid execution_type: '{execution_type}'. "
            f"Must be one of: {', '.join(valid_execution_types)}"
        )

    # If executable, validate executable-specific fields
    if execution_type == "executable":
        executable_type = frontmatter.get("executable_type")

        if not executable_type:
            errors.append(
                "execution_type 'executable' requires 'executable_type'"
            )
        elif executable_type not in ["python", "bash", "node"]:
            errors.append(
                f"Invalid executable_type: '{executable_type}'. "
                f"Must be 'python', 'bash', or 'node'"
            )

        # Python requires executable_path
        if executable_type == "python":
            if not frontmatter.get("executable_path"):
                errors.append(
                    "executable_type 'python' requires 'executable_path'"
                )

        # Bash requires either executable_path or executable_inline
        if executable_type == "bash":
            has_path = bool(frontmatter.get("executable_path"))
            has_inline = bool(frontmatter.get("executable_inline"))

            if not has_path and not has_inline:
                errors.append(
                    "executable_type 'bash' requires either 'executable_path' "
                    "or 'executable_inline'"
                )

        # Node requires either executable_path or executable_inline
        if executable_type == "node":
            has_path = bool(frontmatter.get("executable_path"))
            has_inline = bool(frontmatter.get("executable_inline"))

            if not has_path and not has_inline:
                errors.append(
                    "executable_type 'node' requires either 'executable_path' "
                    "or 'executable_inline'"
                )

    # Validate args structure
    args = frontmatter.get("args", [])
    if args:
        if not isinstance(args, list):
            errors.append("'args' must be a list")
        else:
            for i, arg in enumerate(args):
                if not isinstance(arg, dict):
                    errors.append(f"args[{i}]: must be a dictionary")
                    continue

                if "name" not in arg:
                    errors.append(f"args[{i}]: missing 'name' field")

                arg_type = arg.get("type", "string")
                if arg_type not in ["string", "boolean", "integer"]:
                    errors.append(
                        f"args[{i}]: invalid type '{arg_type}'. "
                        f"Must be 'string', 'boolean', or 'integer'"
                    )

    # Validate aliases if present
    aliases = frontmatter.get("aliases", [])
    if aliases:
        if not isinstance(aliases, list):
            errors.append("'aliases' must be a list")
        elif not all(isinstance(a, str) for a in aliases):
            errors.append("'aliases' must be a list of strings")

    if errors:
        raise ValidationError(errors)

    return frontmatter


def get_handler_info(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Extract handler information from frontmatter.

    Args:
        frontmatter: Validated frontmatter

    Returns:
        Dictionary with handler information:
        - type: 'prompt', 'python', 'bash', 'node', 'template'
        - path: handler module path (for python, node) or script path (for bash, node)
        - inline: inline script (for bash, node)
    """
    execution_type = frontmatter.get("execution_type", "prompt")

    if execution_type == "prompt":
        return {"type": "prompt"}

    if execution_type == "executable":
        executable_type = frontmatter.get("executable_type", "python")

        if executable_type == "python":
            return {
                "type": "python",
                "path": frontmatter.get("executable_path", ""),
            }
        elif executable_type == "bash":
            return {
                "type": "bash",
                "path": frontmatter.get("executable_path", ""),
                "inline": frontmatter.get("executable_inline", ""),
            }
        elif executable_type == "node":
            return {
                "type": "node",
                "path": frontmatter.get("executable_path", ""),
                "inline": frontmatter.get("executable_inline", ""),
            }

    if execution_type == "template":
        return {"type": "template"}

    return {"type": "unknown"}
