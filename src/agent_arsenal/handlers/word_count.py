"""Word count handler."""


def handle_word_count(text: str = "", chars: bool = False, lines: bool = False) -> str:
    """Count words, characters, and lines in text.

    Args:
        text: Text to count (use - for stdin)
        chars: Include character count
        lines: Include line count

    Returns:
        Count results as string
    """
    if not text:
        return "Error: No text provided"

    # Count words
    words = len(text.split())
    result_parts = [f"Words: {words}"]

    # Count characters if requested
    if chars:
        result_parts.append(f"Characters: {len(text)}")

    # Count lines if requested
    if lines:
        # Count non-empty lines
        non_empty_lines = [line for line in text.split("\n") if line.strip()]
        result_parts.append(f"Lines: {len(non_empty_lines)}")

    return "\n".join(result_parts)
