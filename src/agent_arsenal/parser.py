"""Parser for markdown command files with YAML frontmatter."""

from pathlib import Path
from typing import Tuple, Dict, Any
import re


def parse_markdown_command(file_path: Path) -> Tuple[Dict[str, Any], str]:
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

    import yaml

    try:
        frontmatter = yaml.safe_load(frontmatter_str) if frontmatter_str else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing frontmatter in {file_path}: {e}")

    return frontmatter or {}, body


def split_frontmatter(content: str) -> Tuple[str, str]:
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


def validate_frontmatter(frontmatter: Dict[str, Any]) -> Dict[str, Any]:
    """Validate frontmatter against schema.

    Args:
        frontmatter: Parsed frontmatter dictionary

    Returns:
        Validated frontmatter

    Raises:
        ValidationError: If frontmatter is invalid
    """
    # TODO: Implement validation
    # - Check required fields (name, description)
    # - Validate execution_type enum
    # - Validate args structure
    pass
