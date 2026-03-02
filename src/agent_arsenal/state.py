"""State and context management for Agent Arsenal."""

from __future__ import annotations

import json
import logging
import threading
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Scope(Enum):
    """Context scope for state storage."""

    SESSION = "session"  # In-memory only
    PERSISTENT = "persistent"  # Saved to disk
    PROJECT = "project"  # Saved to .arsenal/ in project


class ArsenalState:
    """Singleton state manager for Agent Arsenal.

    Manages context across command invocations with different scopes:
    - SESSION: Temporary data (connections, temp files)
    - PERSISTENT: User-level config and cached data
    - PROJECT: Project-specific state
    """

    _instance: "ArsenalState" | None = None
    _lock = threading.Lock()
    _initialized: bool

    def __new__(cls):
        """Singleton pattern implementation with thread safety."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize state manager."""
        if self._initialized:
            return

        self._session_state: dict[str, Any] = {}
        self._persistent_state: dict[str, Any] = {}
        self._project_state: dict[str, Any] = {}

        self.state_dir = Path.home() / ".agent-arsenal"
        self.state_file = self.state_dir / "state.json"
        self.project_state_file: Path | None = None

        self._initialized = True

    def _get_state_dict(self, scope: Scope) -> dict[str, Any]:
        """Get the state dictionary for a scope.

        Args:
            scope: The scope to get state for

        Returns:
            The state dictionary for the scope

        Raises:
            ValueError: If scope is invalid
        """
        if scope == Scope.SESSION:
            return self._session_state
        elif scope == Scope.PERSISTENT:
            return self._persistent_state
        elif scope == Scope.PROJECT:
            return self._project_state
        else:
            raise ValueError(f"Unknown scope: {scope}")

    def _get_nested_value(self, state_dict: dict[str, Any], key: str) -> Any:
        """Get value from state, supporting dot notation for nested keys.

        Args:
            state_dict: The state dictionary
            key: The key to get (supports dot notation like "a.b.c")

        Returns:
            The value or default if not found
        """
        if "." not in key:
            return state_dict.get(key)

        # Handle nested keys
        keys = key.split(".")
        value: dict[str, Any] | None = state_dict
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value

    def _set_nested_value(self, state_dict: dict[str, Any], key: str, value: Any):
        """Set value in state, supporting dot notation for nested keys.

        Args:
            state_dict: The state dictionary
            key: The key to set (supports dot notation like "a.b.c")
            value: The value to set
        """
        if "." not in key:
            state_dict[key] = value
            return

        # Handle nested keys
        keys = key.split(".")
        current = state_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def _delete_nested_value(self, state_dict: dict[str, Any], key: str) -> bool:
        """Delete value from state, supporting dot notation for nested keys.

        Args:
            state_dict: The state dictionary
            key: The key to delete (supports dot notation like "a.b.c")

        Returns:
            True if deleted, False if not found
        """
        if "." not in key:
            if key in state_dict:
                del state_dict[key]
                return True
            return False

        # Handle nested keys
        keys = key.split(".")
        current = state_dict
        for k in keys[:-1]:
            if k not in current:
                return False
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]
            return True
        return False

    def get(self, key: str, scope: Scope = Scope.SESSION, default: Any = None) -> Any:
        """Retrieve value from state.

        Args:
            key: State key (supports dot notation for nested keys)
            scope: Storage scope
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        state_dict = self._get_state_dict(scope)
        value = self._get_nested_value(state_dict, key)
        return value if value is not None else default

    def set(self, key: str, value: Any, scope: Scope = Scope.SESSION):
        """Store value in state.

        Args:
            key: State key (supports dot notation for nested keys)
            value: Value to store
            scope: Storage scope
        """
        state_dict = self._get_state_dict(scope)
        self._set_nested_value(state_dict, key, value)

    def delete(self, key: str, scope: Scope = Scope.SESSION) -> bool:
        """Remove key from state.

        Args:
            key: State key to remove (supports dot notation for nested keys)
            scope: Storage scope

        Returns:
            True if key was deleted, False if not found
        """
        state_dict = self._get_state_dict(scope)
        return self._delete_nested_value(state_dict, key)

    def persist(self):
        """Save persistent state to disk."""
        # Create state_dir if needed
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON to state_file
        try:
            content = json.dumps(self._persistent_state, indent=2)
            self.state_file.write_text(content, encoding="utf-8")
        except Exception as e:
            # Handle errors gracefully
            raise RuntimeError(f"Failed to persist state: {e}") from e

    def restore(self):
        """Load persistent state from disk."""
        # Check if state_file exists
        if not self.state_file.exists():
            return

        # Load JSON
        try:
            content = self.state_file.read_text(encoding="utf-8")
            if content.strip():
                self._persistent_state = json.loads(content)
        except json.JSONDecodeError as e:
            # Reset to empty on decode error
            self._persistent_state = {}
            raise RuntimeError(f"Failed to restore state: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to restore state: {e}") from e

    def clear(self, scope: Scope | None = None):
        """Clear state for given scope (or all if None).

        Args:
            scope: Scope to clear, or None for all scopes
        """
        if scope is None:
            # Clear all scopes
            self._session_state.clear()
            self._persistent_state.clear()
            self._project_state.clear()
        elif scope == Scope.SESSION:
            self._session_state.clear()
        elif scope == Scope.PERSISTENT:
            self._persistent_state.clear()
        elif scope == Scope.PROJECT:
            self._project_state.clear()

    def set_project(self, project_path: Path):
        """Set current project for PROJECT scope.

        Args:
            project_path: Path to project root
        """
        # Look for .arsenal/ directory in project
        arsenal_dir = project_path / ".arsenal"

        if arsenal_dir.exists() and arsenal_dir.is_dir():
            self.project_state_file = arsenal_dir / "state.json"

            # Load project-specific state if exists
            if self.project_state_file.exists():
                try:
                    content = self.project_state_file.read_text(encoding="utf-8")
                    if content.strip():
                        self._project_state = json.loads(content)
                except json.JSONDecodeError:
                    self._project_state = {}
        else:
            self.project_state_file = None
            self._project_state = {}

    def persist_project(self):
        """Save project state to disk if project is set."""
        if self.project_state_file:
            self.project_state_file.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self._project_state, indent=2)
            self.project_state_file.write_text(content, encoding="utf-8")

    def list_keys(self, scope: Scope = Scope.SESSION) -> list[str]:
        """List all keys in the given scope.

        Args:
            scope: The scope to list keys from

        Returns:
            List of keys (includes nested keys in dot notation)
        """
        state_dict = self._get_state_dict(scope)

        def _get_all_keys(d: dict[str, Any], prefix: str = "") -> list[str]:
            keys = []
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                if isinstance(value, dict):
                    keys.extend(_get_all_keys(value, full_key))
            return keys

        return _get_all_keys(state_dict)


# Global state instance
state = ArsenalState()

# Auto-restore persistent state on module load
try:
    state.restore()
except Exception as e:
    logger.warning("Failed to restore persistent state: %s", e)
