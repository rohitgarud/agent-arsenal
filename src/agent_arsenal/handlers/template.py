"""Template handler."""

import json
import re


def handle_template(template: str = "", values: str = "") -> str:
    """Simple template substitution.

    Args:
        template: Template string with {{variable}} placeholders
        values: JSON object with variable values

    Returns:
        Rendered template
    """
    if not template:
        return "Error: No template provided"

    if not values:
        return "Error: No values provided (use JSON format)"

    # Parse values JSON
    try:
        values_dict = json.loads(values)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in values: {e}"

    # Replace placeholders
    result = template
    for key, value in values_dict.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))

    # Check for unreplaced placeholders
    remaining = re.findall(r"\{\{(\w+)\}\}", result)
    if remaining:
        return f"Error: Missing values for: {', '.join(set(remaining))}"

    return result
