"""Shared utilities for JSON file operations."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONStore:
    """Simple JSON file storage with atomic writes.

    Provides a consistent interface for reading and writing JSON data
    to files with proper error handling and atomic write support.

    Example:
        store = JSONStore(Path.home() / ".arsenal" / "settings.json")
        data = store.load()
        data["new_key"] = "new_value"
        store.save(data)
    """

    def __init__(self, file_path: Path):
        """Initialize the JSON store.

        Args:
            file_path: Path to the JSON file to read/write
        """
        self.file_path = file_path

    def load(self) -> dict[str, Any]:
        """Load data from JSON file.

        If the file doesn't exist, returns an empty dictionary.
        If the file contains invalid JSON, logs a warning and returns
        an empty dictionary.

        Returns:
            Dictionary containing the loaded data, or empty dict on error
        """
        if not self.file_path.exists():
            return {}

        try:
            content = self.file_path.read_text(encoding="utf-8")
            if not content.strip():
                return {}
            data: dict[str, Any] = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in %s: %s", self.file_path, e)
            return {}
        except OSError as e:
            logger.error("Failed to read %s: %s", self.file_path, e)
            return {}

    def save(self, data: dict[str, Any]) -> None:
        """Save data to JSON file with atomic write.

        Creates parent directories if they don't exist.
        Writes to a temporary file first, then renames to the target
        file (atomic on POSIX systems).

        Args:
            data: Dictionary to save as JSON

        Raises:
            IOError: If the file cannot be written
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first, then rename (atomic on POSIX)
        temp_path = self.file_path.with_suffix(".tmp")
        try:
            temp_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            temp_path.replace(self.file_path)
        except OSError as e:
            logger.error("Failed to write %s: %s", self.file_path, e)
            if temp_path.exists():
                temp_path.unlink()
            raise

    def exists(self) -> bool:
        """Check if the JSON file exists.

        Returns:
            True if the file exists, False otherwise
        """
        return self.file_path.exists()

    def delete(self) -> bool:
        """Delete the JSON file if it exists.

        Returns:
            True if the file was deleted, False if it didn't exist
        """
        if self.file_path.exists():
            try:
                self.file_path.unlink()
                return True
            except OSError as e:
                logger.error("Failed to delete %s: %s", self.file_path, e)
                return False
        return False
