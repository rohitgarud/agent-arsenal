"""Cache management for command results."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent_arsenal.executor import CommandResult

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry stored in cache.json."""

    key: str  # SHA256 hash
    command_path: str  # Original path for mtime check
    execution_type: str  # prompt/python/bash/node/template
    args_hash: str  # Hash of args for debugging
    result_success: bool  # Serialized result.success
    result_output: str  # Serialized result.output
    result_error: str | None  # Serialized result.error
    result_metadata: dict[str, Any]  # Serialized result.metadata
    created_at: str  # ISO 8601 timestamp
    ttl_seconds: int  # Time-to-live in seconds
    file_mtime: float  # Command file mtime at creation

    def to_command_result(self) -> CommandResult:
        """Convert CacheEntry back to CommandResult."""
        # Import here to avoid circular dependency
        from agent_arsenal.executor import CommandResult

        return CommandResult(
            success=self.result_success,
            output=self.result_output,
            error=self.result_error,
            metadata=self.result_metadata,
        )


class CacheManager:
    """Manages command result cache with TTL and mtime validation."""

    _instance: CacheManager | None = None

    def __init__(
        self,
        cache_dir: Path | None = None,
        default_ttl: int = 3600,
    ) -> None:
        """Initialize CacheManager.

        Args:
            cache_dir: Override cache directory (default: ~/.agent-arsenal)
            default_ttl: Default TTL in seconds (default: 3600 = 1 hour)
        """
        # Enforce singleton: set instance if none exists
        if CacheManager._instance is None:
            CacheManager._instance = self

        self.cache_dir = cache_dir or Path.home() / ".agent-arsenal"
        self.cache_file = self.cache_dir / "cache.json"
        self._cache: dict[str, CacheEntry] = {}
        self._enabled: bool = True
        self._default_ttl: int = default_ttl
        self._load()

    @classmethod
    def get_instance(cls) -> CacheManager:
        """Lazy singleton initialization."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable caching."""
        self._enabled = enabled

    def get_default_ttl(self) -> int:
        """Get the default TTL."""
        return self._default_ttl

    def set_default_ttl(self, ttl: int) -> None:
        """Set the default TTL."""
        self._default_ttl = ttl

    def generate_key(
        self,
        command_path: Path,
        args: dict[str, Any],
        execution_type: str = "prompt",
    ) -> str:
        """Generate a cache key from command path, args, and execution type.

        Args:
            command_path: Path to the command .md file
            args: Command arguments
            execution_type: Type of execution (prompt, python, bash, etc.)

        Returns:
            SHA256 hash as hex string
        """
        # Create deterministic string representation
        key_parts = [
            str(command_path.resolve()),
            execution_type,
        ]
        # Add sorted args for deterministic ordering
        for k, v in sorted(args.items()):
            key_parts.append(f"{k}={v}")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, key: str, command_path: Path) -> CommandResult | None:
        """Get cached result if valid (not expired, file unchanged).

        Args:
            key: Cache key (SHA256 hash)
            command_path: Path to command file for mtime validation

        Returns:
            CommandResult if cache hit and valid, None otherwise
        """
        if not self._enabled:
            return None

        entry = self._cache.get(key)
        if entry is None:
            return None

        # Check TTL expiry
        try:
            created = datetime.fromisoformat(entry.created_at)
            age_seconds = (datetime.now() - created).total_seconds()
            if age_seconds > entry.ttl_seconds:
                # Expired - remove from cache
                del self._cache[key]
                self._save()
                return None
        except ValueError:
            # Invalid timestamp - remove entry
            del self._cache[key]
            self._save()
            return None

        # Check file modification time
        if command_path.exists():
            current_mtime = command_path.stat().st_mtime
            if current_mtime != entry.file_mtime:
                # File changed - invalidate
                del self._cache[key]
                self._save()
                return None
        else:
            # File no longer exists - invalidate
            del self._cache[key]
            self._save()
            return None

        return entry.to_command_result()

    def set(
        self,
        key: str,
        result: CommandResult,
        ttl: int | None = None,
        command_path: Path | None = None,
        execution_type: str = "prompt",
    ) -> None:
        """Store result in cache.

        Args:
            key: Cache key (SHA256 hash)
            result: CommandResult to cache
            ttl: TTL in seconds (uses default if None)
            command_path: Path to command file (for mtime tracking)
            execution_type: Type of execution
        """
        if not self._enabled:
            return

        if command_path is None:
            raise ValueError("command_path is required to set cache entry")

        # Don't cache errors (per design decision)
        if not result.success:
            return

        args_hash = hashlib.sha256(
            json.dumps(result.metadata or {}, sort_keys=True).encode()
        ).hexdigest()[:16]

        entry = CacheEntry(
            key=key,
            command_path=str(command_path),
            execution_type=execution_type,
            args_hash=args_hash,
            result_success=result.success,
            result_output=result.output,
            result_error=result.error,
            result_metadata=result.metadata or {},
            created_at=datetime.now().isoformat(),
            ttl_seconds=ttl or self._default_ttl,
            file_mtime=command_path.stat().st_mtime if command_path.exists() else 0.0,
        )

        self._cache[key] = entry
        self._save()

    def invalidate(self, key: str) -> bool:
        """Remove specific entry from cache.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and removed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        self._save()
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with entry_count, enabled, default_ttl
        """
        return {
            "entry_count": len(self._cache),
            "enabled": self._enabled,
            "default_ttl": self._default_ttl,
        }

    def _load(self) -> None:
        """Load cache from disk on startup."""
        if not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            if not content.strip():
                return

            data = json.loads(content)
            entries_data = data.get("entries", {})

            for key, entry_data in entries_data.items():
                try:
                    self._cache[key] = CacheEntry(
                        key=entry_data["key"],
                        command_path=entry_data["command_path"],
                        execution_type=entry_data["execution_type"],
                        args_hash=entry_data["args_hash"],
                        result_success=entry_data["result"]["success"],
                        result_output=entry_data["result"]["output"],
                        result_error=entry_data["result"].get("error"),
                        result_metadata=entry_data["result"].get("metadata", {}),
                        created_at=entry_data["created_at"],
                        ttl_seconds=entry_data["ttl_seconds"],
                        file_mtime=entry_data["file_mtime"],
                    )
                except (KeyError, TypeError) as e:
                    logger.warning(f"Skipping invalid cache entry: {e}")
                    continue

        except json.JSONDecodeError as e:
            # Corrupt cache - start fresh
            logger.warning(f"Corrupt cache file, starting fresh: {e}")
            self._cache = {}
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self._cache = {}

    def _save(self) -> None:
        """Persist cache to disk (atomic write)."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Build entries dict for serialization
            entries_dict: dict[str, dict[str, Any]] = {}
            for key, entry in self._cache.items():
                entries_dict[key] = {
                    "key": entry.key,
                    "command_path": entry.command_path,
                    "execution_type": entry.execution_type,
                    "args_hash": entry.args_hash,
                    "result": {
                        "success": entry.result_success,
                        "output": entry.result_output,
                        "error": entry.result_error,
                        "metadata": entry.result_metadata,
                    },
                    "created_at": entry.created_at,
                    "ttl_seconds": entry.ttl_seconds,
                    "file_mtime": entry.file_mtime,
                }

            data = {
                "_meta": {
                    "version": 1,
                    "created_at": datetime.now().isoformat(),
                    "entry_count": len(entries_dict),
                },
                "entries": entries_dict,
            }

            # Atomic write: temp file + rename
            temp = self.cache_file.with_suffix(".tmp")
            temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temp.replace(self.cache_file)

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
            # Continue without saving - cache is in-memory
