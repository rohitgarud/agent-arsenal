"""URL-safe base64 encoding/decoding handler."""

import base64


def url_safe_base64_encode(input: str = "", decode: bool = False) -> str:
    """Encode or decode using URL-safe base64.

    Args:
        input: Input string to encode/decode
        decode: If True, decode from base64 instead of encoding

    Returns:
        URL-safe base64 encoded/decoded string
    """
    if not input:
        return "Error: No input provided"

    try:
        if decode:
            # Decode from URL-safe base64
            # Replace URL-safe characters back to standard base64
            standard = input.replace("-", "+").replace("_", "/")
            # Add padding if needed
            padding = 4 - (len(standard) % 4)
            if padding != 4:
                standard += "=" * padding
            return base64.b64decode(standard).decode("utf-8")
        else:
            # Encode to URL-safe base64
            result = base64.b64encode(input.encode("utf-8")).decode("ascii")
            # Replace standard base64 characters with URL-safe
            return result.replace("+", "-").replace("/", "_").rstrip("=")
    except Exception as e:
        return f"Error: {e}"
