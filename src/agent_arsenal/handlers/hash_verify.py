"""Hash verification handler."""
import hashlib


def hash_verify(text: str, algorithm: str = "sha256", verify: str = "") -> str:
    """Generate or verify hash digest.

    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        verify: Expected hash to verify against

    Returns:
        Generated hash or verification result
    """
    if not text:
        return "Error: Text is required"

    # Normalize algorithm
    algorithm = algorithm.lower()
    valid_algos = {"md5", "sha1", "sha256", "sha512"}

    if algorithm not in valid_algos:
        return f"Error: Invalid algorithm. Supported: {', '.join(valid_algos)}"

    # Generate hash
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    computed_hash = hasher.hexdigest()

    if verify:
        # Verification mode
        verify = verify.lower()
        if computed_hash == verify:
            return "✓ Hash matches!\n\n" + computed_hash
        else:
            return f"✗ Hash does NOT match!\n\nExpected: {verify}\nComputed:  {computed_hash}"

    # Just return the computed hash
    return computed_hash
