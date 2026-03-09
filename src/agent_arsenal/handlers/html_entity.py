"""HTML entity encoding/decoding handler."""

import html


def html_entity_encode(input: str = "", decode: bool = False) -> str:
    """Encode or decode HTML entities.

    Args:
        input: Input string to encode/decode
        decode: If True, decode HTML entities instead of encoding

    Returns:
        HTML entity encoded/decoded string
    """
    if not input:
        return "Error: No input provided"

    try:
        if decode:
            # Decode HTML entities
            return html.unescape(input)
        else:
            # Encode to HTML entities
            return html.escape(input)
    except Exception as e:
        return f"Error: {e}"
