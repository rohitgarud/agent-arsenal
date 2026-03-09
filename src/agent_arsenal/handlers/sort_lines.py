"""Sort lines handler."""


def handle_sort_lines(
    text: str = "",
    reverse: bool = False,
    numeric: bool = False,
    unique: bool = False,
) -> str:
    """Sort lines of text.

    Args:
        text: Text to sort (use - for stdin)
        reverse: Sort in reverse order
        numeric: Sort numerically
        unique: Remove duplicate lines

    Returns:
        Sorted text
    """
    if not text:
        return "Error: No text provided"

    # Split into lines
    lines = text.splitlines()

    # Remove duplicates if requested
    if unique:
        lines = list(dict.fromkeys(lines))

    # Sort
    if numeric:
        try:
            lines = sorted(lines, key=lambda x: int(x), reverse=reverse)
        except ValueError:
            # Fall back to alphabetical if not all numeric
            lines = sorted(lines, key=lambda x: x.strip(), reverse=reverse)
    else:
        lines = sorted(lines, key=lambda x: x.strip(), reverse=reverse)

    return "\n".join(lines)
