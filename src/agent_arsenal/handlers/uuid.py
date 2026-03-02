"""UUID command handler."""

import uuid as uuid_module


def _uuid7() -> str:
    """Generate a UUID v7 (time-ordered).

    UUID v7 is not in Python standard library yet, so we implement it.
    """
    import random
    import time

    # Get current timestamp in milliseconds
    ts = int(time.time() * 1000)

    # UUID v7 format:
    # - 48 bits for timestamp (milliseconds)
    # - 4 bits for version (7)
    # - 2 bits for variant (RFC 4122)
    # - 62 bits for random data

    # Pack timestamp into 6 bytes (48 bits)
    ts_bytes = ts.to_bytes(6, byteorder="big")

    # Generate random bytes
    rand_bytes = random.randbytes(10)

    # Build the UUID bytes
    uuid_bytes = bytearray(16)

    # 0-5: timestamp (48 bits)
    uuid_bytes[0:6] = ts_bytes

    # 6: version = 7 in upper 4 bits
    uuid_bytes[6] = 0x70 | (uuid_bytes[6] & 0x0F)

    # 7: unchanged (lower timestamp bits)

    # 8: variant = RFC 4122 (0x8, 0x9, 0xA, 0xB) in upper 2 bits
    uuid_bytes[8] = 0x80 | (uuid_bytes[8] & 0x3F)

    # 9-15: random from rand_bytes
    uuid_bytes[9:16] = rand_bytes[0:7]

    return str(uuid_module.UUID(bytes=bytes(uuid_bytes)))


def handle_uuid(
    version: int = 4,
    uppercase: bool = False,
    count: int = 1,
) -> str:
    """Generate UUIDs.

    Args:
        version: UUID version (4 or 7)
        uppercase: Convert to uppercase
        count: Number of UUIDs to generate

    Returns:
        Generated UUID(s)
    """
    if version not in (4, 7):
        return f"Error: UUID version must be 4 or 7, got {version}"

    if count < 1:
        return f"Error: Count must be at least 1, got {count}"

    if count > 1000:
        return f"Error: Count cannot exceed 1000, got {count}"

    uuids = []
    for _ in range(count):
        if version == 4:
            u = str(uuid_module.uuid4())
        else:
            u = _uuid7()

        uuids.append(u)

    result = "\n".join(uuids)

    if uppercase:
        result = result.upper()

    return result
