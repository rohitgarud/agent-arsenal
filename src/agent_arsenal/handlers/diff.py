"""Diff handler."""

import difflib


def handle_diff(text1: str = "", text2: str = "", context: int = 3) -> str:
    """Compare two texts and show differences.

    Args:
        text1: First text (use - for stdin)
        text2: Second text (use - for stdin)
        context: Number of context lines to show

    Returns:
        Diff output
    """
    if not text1 or not text2:
        return "Error: Both text1 and text2 are required"

    # Split into lines
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    # Generate diff
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile="text1",
        tofile="text2",
        lineterm="",
        n=context,
    )

    result = list(diff)
    if not result:
        return "No differences found"

    return "".join(result)
