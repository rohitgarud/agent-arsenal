"""Configuration management for Agent Arsenal.

Manages external command directory configuration stored in ~/.arsenal/settings.json
"""

import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG: dict = {"command_directories": []}


def get_config_path() -> Path:
    """Get the path to the settings config file.

    Returns:
        Path to ~/.arsenal/settings.json
    """
    return Path.home() / ".arsenal" / "settings.json"


def _ensure_config_dir() -> Path:
    """Ensure the config directory exists.

    Returns:
        Path to the config directory

    Raises:
        PermissionError: If the directory cannot be created
    """
    config_path = get_config_path()
    config_dir = config_path.parent

    if not config_dir.exists():
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create config directory {config_dir}: {e}"
            ) from e

    return config_dir


def load_config() -> dict:
    """Load configuration from the config file.

    If the file doesn't exist or is invalid, returns default config.

    Returns:
        Configuration dictionary

    Raises:
        PermissionError: If the file exists but cannot be read due to permissions
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {"command_directories": []}

    try:
        content = config_path.read_text(encoding="utf-8")
    except PermissionError as e:
        logger.warning(f"Cannot read config file {config_path}: {e}")
        return {"command_directories": []}

    if not content.strip():
        return {"command_directories": []}

    try:
        config = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            f"Invalid JSON in config file {config_path}: {e}. Resetting to default."
        )
        return {"command_directories": []}

    # Ensure command_directories exists
    if "command_directories" not in config:
        config["command_directories"] = []

    # Ensure it's a list
    if not isinstance(config["command_directories"], list):
        logger.warning(
            "Invalid command_directories format. Resetting to default."
        )
        config["command_directories"] = []

    return config


def save_config(config: dict) -> None:
    """Save configuration to the config file.

    Args:
        config: Configuration dictionary to save

    Raises:
        PermissionError: If the config file cannot be written
    """
    _ensure_config_dir()
    config_path = get_config_path()

    try:
        config_path.write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8"
        )
    except PermissionError as e:
        raise PermissionError(
            f"Cannot write config file {config_path}: {e}"
        ) from e


def get_command_directories() -> List[Path]:
    """Get the list of configured external command directories.

    Returns:
        List of Path objects for configured directories
    """
    config = load_config()
    dirs = config.get("command_directories", [])
    return [Path(d) for d in dirs if d]


def add_command_directory(path: Path | str) -> bool:
    """Add an external command directory to the configuration.

    If the path is already registered, this succeeds silently (idempotent).

    Args:
        path: Path to the external command directory

    Returns:
        True if the directory was added, False if it was already present
    """
    # Accept both Path and string
    if isinstance(path, str):
        path = Path(path)

    # Convert to absolute path if relative
    if not path.is_absolute():
        path = path.resolve()

    config = load_config()
    dirs = config.get("command_directories", [])

    # Check for existing entry (case-sensitive for exact match)
    path_str = str(path)
    for existing in dirs:
        if Path(existing).resolve() == path:
            # Already exists, silently succeed (idempotent)
            return False

    # Add the new directory
    dirs.append(path_str)
    config["command_directories"] = dirs
    save_config(config)

    logger.info(f"Added command directory: {path}")
    return True


def remove_command_directory(path: Path | str) -> bool:
    """Remove an external command directory from the configuration.

    Args:
        path: Path to the external command directory to remove

    Returns:
        True if the directory was removed, False if it was not found
    """
    # Accept both Path and string
    if isinstance(path, str):
        path = Path(path)

    # Convert to absolute path if relative
    if not path.is_absolute():
        path = path.resolve()

    config = load_config()
    dirs = config.get("command_directories", [])

    # Find and remove the directory
    new_dirs = []
    removed = False

    for existing in dirs:
        if Path(existing).resolve() == path:
            removed = True
            continue
        new_dirs.append(existing)

    if removed:
        config["command_directories"] = new_dirs
        save_config(config)
        logger.info(f"Removed command directory: {path}")

    return removed


def list_command_directories() -> List[Path]:
    """List all configured external command directories.

    Returns:
        List of Path objects for configured directories
    """
    return get_command_directories()
