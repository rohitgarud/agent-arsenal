"""Punycode encoding/decoding handler."""

import codecs


def punycode_encode(input: str = "", decode: bool = False) -> str:
    """Encode or decode punycode (internationalized domain names).

    Args:
        input: Domain name to encode/decode
        decode: If True, decode from punycode instead of encoding

    Returns:
        Punycode encoded/decoded string
    """
    if not input:
        return "Error: No input provided"

    try:
        if decode:
            # Decode from punycode
            # Add the ACE prefix if not present for decoding
            if not input.startswith("xn--"):
                input = "xn--" + input
            return codecs.decode(input, "idna").decode("ascii")  # type: ignore[call-overload]
        else:
            # Encode to punycode
            return codecs.encode(input, "idna").decode("ascii")
    except Exception as e:
        return f"Error: Invalid domain name: {e}"
