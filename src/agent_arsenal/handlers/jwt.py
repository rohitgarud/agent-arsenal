"""JWT command handler."""

import base64
import json


def handle_jwt(
    token: str = "",
    part: str = "all",
) -> str:
    """Decode JWT tokens and display their contents.

    Note: This only DECODES tokens for inspection. It does NOT verify signatures.

    Args:
        token: JWT token to decode
        part: Which part to show (header, payload, signature, all)

    Returns:
        Decoded JWT parts
    """
    if not token:
        return "Error: No token provided"

    part = part.lower()

    # Split the token into parts
    parts = token.split(".")

    if len(parts) != 3:
        return f"Error: Invalid JWT format. Expected 3 parts, got {len(parts)}"

    header_b64, payload_b64, signature_b64 = parts

    # Decode header
    try:
        header_json = base64.urlsafe_b64decode(header_b64 + "==").decode("utf-8")
        header = json.loads(header_json)
    except Exception as e:
        return f"Error: Failed to decode header: {e}"

    # Decode payload
    try:
        payload_json = base64.urlsafe_b64decode(payload_b64 + "==").decode("utf-8")
        payload = json.loads(payload_json)
    except Exception as e:
        return f"Error: Failed to decode payload: {e}"

    # Format output
    output_parts = []

    if part in ("header", "all"):
        output_parts.append("=== HEADER ===")
        output_parts.append(json.dumps(header, indent=2))

    if part in ("payload", "all"):
        output_parts.append("=== PAYLOAD ===")
        output_parts.append(json.dumps(payload, indent=2))

    if part in ("signature", "all"):
        output_parts.append("=== SIGNATURE ===")
        output_parts.append(f"(signature not verified: {signature_b64})")

    return "\n\n".join(output_parts)
