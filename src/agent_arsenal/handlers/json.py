"""JSON command handler."""

import json
import sys


def handle_json(
    input: str = "",
    indent: int = 2,
    minify: bool = False,
    validate: bool = False,
) -> str:
    """Format, validate, or minify JSON.

    Args:
        input: Input JSON string (use - for stdin)
        indent: Indentation spaces (0 for minified)
        minify: Minify output
        validate: Only validate, no output

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
    if validate:
        return "Valid JSON"
    
    # Determine indent
    if minify:
        indent = 0
    
    # Format JSON
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        return f"Error: {e}"