"""Configuration management for Agent Arsenal.

Manages external command directory configuration stored in ~/.arsenal/settings.json
and sandbox configuration for secure command execution.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from agent_arsenal.sandbox import SandboxConfig, SandboxPermissions

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG: dict[str, Any] = {"command_directories": []}


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


def load_config() -> dict[str, Any]:
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
        logger.warning("Cannot read config file %s: %s", config_path, e)
        return {"command_directories": []}

    if not content.strip():
        return {"command_directories": []}

    try:
        config: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            "Invalid JSON in config file %s: %s. Resetting to default.",
            config_path,
            e,
        )
        return {"command_directories": []}

    # Ensure command_directories exists
    if "command_directories" not in config:
        config["command_directories"] = []

    # Ensure it's a list
    if not isinstance(config["command_directories"], list):
        logger.warning("Invalid command_directories format. Resetting to default.")
        config["command_directories"] = []

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to the config file.

    Args:
        config: Configuration dictionary to save

    Raises:
        PermissionError: If the config file cannot be written
    """
    _ensure_config_dir()
    config_path = get_config_path()

    try:
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(f"Cannot write config file {config_path}: {e}") from e


def get_user_commands_dir() -> Path:
    """Get the default user commands directory.

    Returns:
        Path to ~/.arsenal/commands
    """
    return Path.home() / ".arsenal" / "commands"


def get_command_directories() -> list[Path]:
    """Get the list of configured external command directories.

    Always includes ~/.arsenal/commands if it exists (auto-discovery).

    Returns:
        List of Path objects for configured directories
    """
    config = load_config()
    dirs = config.get("command_directories", [])

    # Auto-add ~/.arsenal/commands if it exists
    user_commands_dir = get_user_commands_dir()
    if user_commands_dir.exists() and user_commands_dir.is_dir():
        # Add if not already in config
        if not any(Path(d).resolve() == user_commands_dir for d in dirs):
            dirs.append(str(user_commands_dir))

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

    logger.info("Added command directory: %s", path)
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
        logger.info("Removed command directory: %s", path)

    return removed


def list_command_directories() -> list[Path]:
    """List all configured external command directories.

    Returns:
        List of Path objects for configured directories
    """
    return get_command_directories()


def should_watch() -> bool:
    """Check if watch mode should be enabled by default.

    Checks the ARSENAL_WATCH environment variable.
    Returns True for "1", "true", "yes" (case-insensitive).

    Returns:
        True if watch mode should be enabled by default
    """
    watch_env = os.environ.get("ARSENAL_WATCH", "").lower()
    return watch_env in ("1", "true", "yes")


# =============================================================================
# Sandbox Configuration Functions
# =============================================================================


def load_sandbox_config() -> SandboxConfig:
    """Load sandbox configuration from ~/.arsenal/settings.json.

    If the sandbox config section doesn't exist or is invalid,
    returns a SandboxConfig with default values.

    Also checks if Deno is available and disables sandbox if not.

    Returns:
        SandboxConfig instance with loaded or default values
    """
    config_path = get_config_path()

    if not config_path.exists():
        return SandboxConfig()

    try:
        content = config_path.read_text(encoding="utf-8")
    except PermissionError as e:
        logger.warning("Cannot read config file %s: %s", config_path, e)
        return SandboxConfig()

    if not content.strip():
        return SandboxConfig()

    try:
        config: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            "Invalid JSON in config file %s: %s. Using default sandbox config.",
            config_path,
            e,
        )
        return SandboxConfig()

    sandbox_data = config.get("sandbox", {})

    # Parse enabled flag
    enabled = sandbox_data.get("enabled", True)

    # Parse timeout
    timeout_seconds = sandbox_data.get("timeout_seconds", 30)

    # Parse default permissions
    perms_data = sandbox_data.get("default_permissions", {})
    default_permissions = SandboxPermissions(
        allow_read=perms_data.get("allow_read", []),
        allow_write=perms_data.get("allow_write", []),
        allow_net=perms_data.get("allow_net", False),
        allow_env=perms_data.get("allow_env", []),
        allow_run=perms_data.get("allow_run", False),
    )

    # Check Deno availability - if not available, warn and disable
    from agent_arsenal.sandbox import DenoSandboxExecutor

    temp_config = SandboxConfig(
        enabled=enabled,
        timeout_seconds=timeout_seconds,
        default_permissions=default_permissions,
    )
    executor = DenoSandboxExecutor(temp_config)
    if not executor._check_deno_available():
        logger.warning(
            "Deno is not installed. Sandbox will be disabled. "
            "Install via: curl -fsSL https://deno.land/x/install/install.sh | sh"
        )
        return SandboxConfig(enabled=False)

    return SandboxConfig(
        enabled=enabled,
        timeout_seconds=timeout_seconds,
        default_permissions=default_permissions,
    )


def save_sandbox_config(config: SandboxConfig) -> None:
    """Save sandbox configuration to ~/.arsenal/settings.json.

    Creates the ~/.arsenal directory if it doesn't exist.

    Args:
        config: SandboxConfig instance to save

    Raises:
        PermissionError: If the config file cannot be written
    """
    _ensure_config_dir()
    config_path = get_config_path()

    # Load existing config to preserve other settings
    existing_config = load_config()

    # Build sandbox config dict
    perms = config.default_permissions

    # Handle allow_run - can be bool or list of strings
    allow_run_value: bool | list[str]
    if isinstance(perms.allow_run, bool):
        allow_run_value = perms.allow_run
    else:
        allow_run_value = perms.allow_run if perms.allow_run else []

    sandbox_data: dict[str, Any] = {
        "enabled": config.enabled,
        "timeout_seconds": config.timeout_seconds,
        "default_permissions": {
            "allow_read": perms.allow_read,
            "allow_write": perms.allow_write,
            "allow_net": perms.allow_net,
            "allow_env": perms.allow_env,
            "allow_run": allow_run_value,
        },
    }

    # Merge with existing config
    existing_config["sandbox"] = sandbox_data

    try:
        config_path.write_text(
            json.dumps(existing_config, indent=2) + "\n", encoding="utf-8"
        )
    except PermissionError as e:
        raise PermissionError(f"Cannot write config file {config_path}: {e}") from e


def get_sandbox_permissions_for_command(
    frontmatter: dict[str, Any],
    global_config: SandboxConfig,
) -> SandboxPermissions:
    """Merge command-specific and global sandbox permissions.

    Command-specific permissions in frontmatter override global defaults.

    Args:
        frontmatter: Command's frontmatter dict (may contain sandbox_permissions)
        global_config: Global SandboxConfig with default permissions

    Returns:
        Merged SandboxPermissions with command-specific overrides
    """
    # Start with global defaults
    perms = global_config.default_permissions

    # Get command-specific permissions from frontmatter
    cmd_perms_data = frontmatter.get("sandbox_permissions")

    if not cmd_perms_data or not isinstance(cmd_perms_data, dict):
        # No command-specific overrides, return global defaults
        return perms

    # Merge command-specific permissions with global defaults
    return SandboxPermissions(
        allow_read=cmd_perms_data.get("allow_read", perms.allow_read),
        allow_write=cmd_perms_data.get("allow_write", perms.allow_write),
        allow_net=cmd_perms_data.get("allow_net", perms.allow_net),
        allow_env=cmd_perms_data.get("allow_env", perms.allow_env),
        allow_run=cmd_perms_data.get("allow_run", perms.allow_run),
    )
