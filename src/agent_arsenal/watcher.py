"""Hot reload functionality for command files (Phase 2)."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from agent_arsenal.registry import CommandRegistry


class CommandWatcher:
    """Watch commands directory for changes and trigger reload.

    Uses watchfiles library for efficient filesystem monitoring.
    """

    def __init__(self, commands_dir: Path, reload_callback: Callable):
        """Initialize watcher.

        Args:
            commands_dir: Directory to watch
            reload_callback: Function to call on changes
        """
        self.commands_dir = commands_dir
        self.reload_callback = reload_callback
        self._watching = False

    def start(self):
        """Start watching for file changes."""
        # TODO: Implement with watchfiles library
        # - Watch for .md file changes
        # - Debounce rapid changes
        # - Call reload_callback on change
        pass

    def stop(self):
        """Stop watching."""
        # TODO: Implement cleanup
        pass

    def watch(self):
        """Blocking watch loop."""
        # TODO: Implement blocking watch
        # For use with --watch flag
        pass


def enable_hot_reload(commands_dir: Path, registry: "CommandRegistry"):
    """Enable hot reload for command registry.

    Args:
        commands_dir: Commands directory to watch
        registry: Registry to reload on changes
    """
    # TODO: Implement hot reload setup
    # - Create watcher
    # - Start in background thread
    # - Return cleanup function
    pass
