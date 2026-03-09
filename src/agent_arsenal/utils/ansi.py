import re


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from a string.

    Args:
        text: The string containing ANSI escape sequences.

    Returns:
        The string with ANSI escape sequences removed.
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)
