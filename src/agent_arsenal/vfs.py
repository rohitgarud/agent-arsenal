"""Virtual File System (VFS) backed by sqlite3.

This module provides a singleton VFSManager for managing virtual files
with CRUD operations and transaction support.
"""

import json
import logging
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_arsenal.exceptions import VFSTransactionError

logger = logging.getLogger(__name__)


class VFSTransaction:
    """Context manager for VFS transactions."""

    def __init__(self, vfs: "VFSManager"):
        self.vfs = vfs

    def __enter__(self) -> "VFSTransaction":
        self.vfs.begin()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.vfs.rollback()
        else:
            self.vfs.commit()


class VFSManager:
    """Singleton VFS manager backed by sqlite3.

    Provides CRUD operations for virtual files with transaction support.
    Thread-safe through locking mechanisms.
    """

    _instance: "VFSManager | None" = None
    _lock = threading.Lock()

    def __init__(self, db_path: Path) -> None:
        """Initialize VFS manager.

        Args:
            db_path: Path to sqlite3 database file.
        """
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._local_lock = threading.Lock()
        self._in_transaction = False

    @classmethod
    def get_instance(cls, db_path: Path | None = None) -> "VFSManager":
        """Get the singleton VFSManager instance.

        Args:
            db_path: Optional path to database. Creates in memory if not provided.

        Returns:
            The singleton VFSManager instance.
        """
        with cls._lock:
            if cls._instance is None:
                if db_path is None:
                    db_path = Path(":memory:")
                cls._instance = cls(db_path)
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.

        Useful for testing to ensure a fresh instance.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
            cls._instance = None

    def _ensure_connection(self) -> sqlite3.Connection:
        """Ensure database connection exists and initialize schema if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._initialize_schema(self._conn)
        return self._conn

    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize the VFS database schema."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vfs_files (
                path TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def write(self, path: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Write content to a virtual file.

        Args:
            path: Virtual file path.
            content: File content (text).
            metadata: Optional metadata dictionary.

        Raises:
            VFSTransactionError: If in transaction and operation fails.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            now = datetime.utcnow().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None

            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vfs_files (path, content, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, COALESCE((SELECT created_at FROM vfs_files WHERE path = ?), ?), ?)
                    """,
                    (path, content, metadata_json, path, now, now),
                )
                if not self._in_transaction:
                    conn.commit()
            except sqlite3.Error as e:
                if self._in_transaction:
                    raise VFSTransactionError(f"Write failed: {e}") from e
                raise

    def read(self, path: str) -> str | None:
        """Read content from a virtual file.

        Args:
            path: Virtual file path.

        Returns:
            File content, or None if file doesn't exist.

        Raises:
            VFSTransactionError: If in transaction and operation fails.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            try:
                cursor = conn.execute(
                    "SELECT content FROM vfs_files WHERE path = ?",
                    (path,),
                )
                row = cursor.fetchone()
                return row["content"] if row else None
            except sqlite3.Error as e:
                if self._in_transaction:
                    raise VFSTransactionError(f"Read failed: {e}") from e
                raise

    def delete(self, path: str) -> bool:
        """Delete a virtual file.

        Args:
            path: Virtual file path.

        Returns:
            True if file was deleted, False if it didn't exist.

        Raises:
            VFSTransactionError: If in transaction and operation fails.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            try:
                cursor = conn.execute("DELETE FROM vfs_files WHERE path = ?", (path,))
                if not self._in_transaction:
                    conn.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                if self._in_transaction:
                    raise VFSTransactionError(f"Delete failed: {e}") from e
                raise

    def exists(self, path: str) -> bool:
        """Check if a virtual file exists.

        Args:
            path: Virtual file path.

        Returns:
            True if file exists, False otherwise.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            cursor = conn.execute(
                "SELECT 1 FROM vfs_files WHERE path = ? LIMIT 1",
                (path,),
            )
            return cursor.fetchone() is not None

    def list(self, prefix: str = "/") -> list[str]:
        """List virtual files with a given prefix.

        Args:
            prefix: Path prefix to filter by.

        Returns:
            List of matching paths.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            # Ensure prefix ends with % for LIKE matching
            search_prefix = prefix if prefix.endswith("%") or prefix.endswith("/") else prefix + "/"
            if not search_prefix.startswith("/"):
                search_prefix = "/" + search_prefix
            search_prefix = search_prefix.rstrip("/") + "/%"

            cursor = conn.execute(
                "SELECT path FROM vfs_files WHERE path LIKE ? ORDER BY path",
                (search_prefix,),
            )
            return [row["path"] for row in cursor.fetchall()]

    def get_metadata(self, path: str) -> dict[str, Any] | None:
        """Get metadata for a virtual file.

        Args:
            path: Virtual file path.

        Returns:
            Metadata dictionary, or None if file doesn't exist or has no metadata.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            cursor = conn.execute(
                "SELECT metadata FROM vfs_files WHERE path = ?",
                (path,),
            )
            row = cursor.fetchone()
            if row and row["metadata"]:
                return json.loads(row["metadata"])
            return None

    def get_stats(self) -> dict[str, Any]:
        """Get VFS statistics.

        Returns:
            Dictionary with file_count, db_path, and db_size.
        """
        with self._local_lock:
            conn = self._ensure_connection()
            cursor = conn.execute("SELECT COUNT(*) as count FROM vfs_files")
            count = cursor.fetchone()["count"]

            db_size = 0
            if self._db_path != Path(":memory:") and self._db_path.exists():
                db_size = self._db_path.stat().st_size

            return {
                "file_count": count,
                "db_path": str(self._db_path),
                "db_size": db_size,
            }

    def begin(self) -> None:
        """Begin a manual transaction."""
        with self._local_lock:
            conn = self._ensure_connection()
            conn.execute("BEGIN")
            self._in_transaction = True

    def commit(self) -> None:
        """Commit the current transaction."""
        with self._local_lock:
            if self._conn is not None:
                self._conn.execute("COMMIT")
            self._in_transaction = False

    def rollback(self) -> None:
        """Rollback the current transaction."""
        with self._local_lock:
            if self._conn is not None:
                self._conn.execute("ROLLBACK")
            self._in_transaction = False

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for transactions.

        Yields:
            None.

        Note:
            Uses try/finally to ensure proper commit/rollback regardless
            of whether an exception occurs.
        """
        self.begin()
        try:
            yield
        except Exception:
            self.rollback()
            raise
        else:
            self.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
