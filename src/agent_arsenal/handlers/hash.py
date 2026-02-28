"""Hash command handler."""

import base64
import hashlib
import sys


def handle_hash(
    algorithm: str = "sha256",
    input: str = "",
    encoding: str = "utf-8",
) -> str:
    """Compute cryptographic hashes.

    Args:
        algorithm: Hash algorithm (md5, sha256, sha512)
        input: Input string to hash (use - for stdin)
        encoding: Input encoding (utf-8, latin-1, hex, base64)

    Returns:
        Hash digest
    """
    # Read from stdin if requested
    if input == "-":
        input = sys.stdin.read()

    if not input:
        return "Error: No input provided"

    # Get the hash algorithm
    algorithm = algorithm.lower()
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "sha512":
        hasher = hashlib.sha512()
    else:
        return f"Error: Unknown algorithm '{algorithm}'. Supported: md5, sha256, sha512"

    # Decode input based on encoding
    try:
        if encoding == "utf-8":
            data = input.encode("utf-8")
        elif encoding == "latin-1":
            data = input.encode("latin-1")
        elif encoding == "hex":
            data = bytes.fromhex(input)
        elif encoding == "base64":
            data = base64.b64decode(input)
        else:
            return f"Error: Unknown encoding '{encoding}'. Supported: utf-8, latin-1, hex, base64"
    except Exception as e:
        return f"Error: Failed to decode input: {e}"

    # Compute hash
    hasher.update(data)
    return hasher.hexdigest()
