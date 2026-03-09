"""Hex encoding/decoding handler."""


def hex_encode(input: str = "", decode: bool = False) -> str:
    """Encode or decode hexadecimal.

    Args:
        input: Input string to encode/decode
        decode: If True, decode from hex instead of encoding

    Returns:
        Hex encoded/decoded string
    """
    if not input:
        return "Error: No input provided"

    try:
        if decode:
            # Decode from hex
            result = bytes.fromhex(input).decode("utf-8")
            return result
        else:
            # Encode to hex
            return input.encode("utf-8").hex()
    except ValueError as e:
        return f"Error: Invalid hex string: {e}"
    except Exception as e:
        return f"Error: {e}"
