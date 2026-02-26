"""URL command handler."""

import urllib.parse


def handle_url(
    mode: str = "encode",
    input: str = "",
) -> str:
    """URL encode or decode strings.

    Args:
        mode: Operation mode (encode or decode)
        input: Input string to process

    Returns:
        URL encoded/decoded string
    """
    if not input:
        return "Error: No input provided"
    
    mode = mode.lower()
    
    try:
        if mode == "encode":
            return urllib.parse.quote(input)
        elif mode == "decode":
            return urllib.parse.unquote(input)
        else:
            return f"Error: Unknown mode '{mode}'. Use 'encode' or 'decode'"
    except Exception as e:
        return f"Error: {e}"