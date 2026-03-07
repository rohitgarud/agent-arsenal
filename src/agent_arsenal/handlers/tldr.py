"""tldr command handler."""

import shutil
import subprocess

_TLDR_CLIENTS: list[str] = ["tldr", "tlrc"]
_DEFAULT_TIMEOUT: int = 30


def is_tldr_available() -> bool:
    """Check if any tldr client is available in PATH.

    Returns:
        True if tldr or tlrc is available, False otherwise.
    """
    return get_tldr_client() is not None


def get_tldr_client() -> str | None:
    """Get the first available tldr client.

    Returns:
        Name of the first available client (tldr or tlrc), or None if none available.
    """
    for client in _TLDR_CLIENTS:
        if shutil.which(client):
            return client
    return None


def get_installation_instructions() -> str:
    """Get installation instructions for tldr.

    Returns:
        Multi-line string with installation methods.
    """
    return """tldr is not installed. Install it using one of the following methods:

Python:
  pipx install tldr

Rust:
  cargo install tlrc
  # or
  brew install tlrc

Node.js:
  npm install -g tldr

For more information, visit: https://tldr.sh
"""


def handle_tldr(command: str) -> str:
    """Get simplified man page for a CLI command using tldr.

    Args:
        command: CLI command name to look up (e.g., docker, kubectl, git)

    Returns:
        The tldr page content, or installation instructions if not available.
    """
    client = get_tldr_client()

    if client is None:
        return get_installation_instructions()

    try:
        result = subprocess.run(
            [client, command],
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT,
        )

        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 127:
            return f"Command '{command}' not found in tldr pages."
        else:
            return f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return f"Error: tldr command timed out after {_DEFAULT_TIMEOUT} seconds."
    except Exception as e:
        return f"Error running tldr: {str(e)}"
