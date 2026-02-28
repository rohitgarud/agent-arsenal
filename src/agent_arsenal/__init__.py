"""Agent Arsenal - A global CLI tool for coding agents to use in development."""

from agent_arsenal.config import (
    add_command_directory,
    get_command_directories,
    get_config_path,
    get_sandbox_permissions_for_command,
    list_command_directories,
    load_config,
    load_sandbox_config,
    remove_command_directory,
    save_config,
    save_sandbox_config,
    should_watch,
)
from agent_arsenal.sandbox import (
    CommandResult,
    DenoSandboxExecutor,
    SandboxConfig,
    SandboxPermissions,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "get_config_path",
    "load_config",
    "save_config",
    "get_command_directories",
    "add_command_directory",
    "remove_command_directory",
    "list_command_directories",
    "should_watch",
    "load_sandbox_config",
    "save_sandbox_config",
    "get_sandbox_permissions_for_command",
    "SandboxConfig",
    "SandboxPermissions",
    "CommandResult",
    "DenoSandboxExecutor",
]
