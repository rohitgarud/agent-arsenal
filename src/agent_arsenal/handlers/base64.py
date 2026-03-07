"""Base64 command handler."""

import base64
import sys


def handle_base64(
    subcommand: str = "encode",
    input: str = "",
    wrap: int = 0,
) -> str:
    """Encode or decode Base64.

    Args:
        subcommand: Operation subcommand (encode or decode)
        input: Input string (use - for stdin)
        wrap: Wrap output at this column (0 to disable)

    Returns:
        Base64 encoded/decoded string
    """
    # Read from stdin if requested
    if input == "-":
        input = sys.stdin.read().rstrip("\n")

    if not input and subcommand == "encode":
        return "Error: No input provided"

    mode = subcommand.lower()

    try:
        if mode == "encode":
            # Encode to base64
            if isinstance(input, str):
                data = input.encode("utf-8")
            else:
                data = input

            result = base64.b64encode(data).decode("ascii")

            # Wrap if requested
            if wrap > 0:
                result = _wrap_text(result, wrap)

            return result

        elif mode == "decode":
            # Decode from base64
            # Remove any whitespace
            input = input.strip()

            result = base64.b64decode(input).decode("utf-8")
            return result
        else:
            return f"Error: Unknown mode '{mode}'. Use 'encode' or 'decode'"

    except Exception as e:
        return f"Error: {e}"


def _wrap_text(text: str, width: int) -> str:
    """Wrap text at specified width.

    Args:
        text: Text to wrap
        width: Column width

    Returns:
        Wrapped text
    """
    lines = []
    for i in range(0, len(text), width):
        lines.append(text[i : i + width])
    return "\n".join(lines)
