"""JSON command handler."""

import json
import sys


def handle_json(
    subcommand: str = "format",
    input: str = "",
    indent: int | None = 2,
) -> str:
    """Format, validate, or minify JSON.

    Args:
        subcommand: Operation subcommand (format, validate, minify)
        input: Input JSON string (use - for stdin)
        indent: Indentation spaces (0 for minified)

    Returns:
        Formatted/validated JSON
    """
    # Read from stdin if requested
    if input == "-":
        input = sys.stdin.read()

    if not input:
        return "Error: No input provided"

    # Parse JSON
    try:
        data = json.loads(input)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON: {e}"

    # Validation only
    if subcommand == "validate":
        return "Valid JSON"

    # Minify if requested
    if subcommand == "minify":
        indent = None

    # Format JSON
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        return f"Error: {e}"
