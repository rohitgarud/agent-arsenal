"""Unit tests for VFS (Virtual File System)."""

from pathlib import Path

import pytest

from agent_arsenal.vfs import VFSManager


@pytest.fixture
def temp_vfs(tmp_path: Path) -> VFSManager:
    """Create a VFSManager instance with a temporary database."""
    VFSManager.reset_instance()
    db_path = tmp_path / "test_vfs.db"
    vfs = VFSManager.get_instance(db_path)
    yield vfs
    vfs.close()
    VFSManager.reset_instance()


@pytest.fixture
def vfs(temp_vfs: VFSManager) -> VFSManager:
    """Alias for temp_vfs fixture."""
    return temp_vfs


# Singleton tests
class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_instance_returns_singleton(self, tmp_path: Path) -> None:
        """Verify get_instance returns the same instance."""
        VFSManager.reset_instance()
        db_path = tmp_path / "singleton_test.db"
        vfs1 = VFSManager.get_instance(db_path)
        vfs2 = VFSManager.get_instance(db_path)
        assert vfs1 is vfs2
        vfs1.close()
        VFSManager.reset_instance()

    def test_reset_instance_creates_new_instance(self, tmp_path: Path) -> None:
        """Verify reset_instance creates a new singleton."""
        VFSManager.reset_instance()
        db_path = tmp_path / "reset_test.db"
        vfs1 = VFSManager.get_instance(db_path)
        VFSManager.reset_instance()
        vfs2 = VFSManager.get_instance(db_path)
        assert vfs1 is not vfs2
        vfs2.close()
        VFSManager.reset_instance()


# CRUD tests
class TestCRUD:
    """Tests for CRUD operations."""

    def test_write_creates_file(self, vfs: VFSManager) -> None:
        """Verify write creates a new virtual file."""
        vfs.write("/test.txt", "Hello World")
        content = vfs.read("/test.txt")
        assert content == "Hello World"

    def test_write_updates_existing_file(self, vfs: VFSManager) -> None:
        """Verify write updates an existing file."""
        vfs.write("/test.txt", "Original")
        vfs.write("/test.txt", "Updated")
        content = vfs.read("/test.txt")
        assert content == "Updated"

    def test_write_with_metadata(self, vfs: VFSManager) -> None:
        """Verify write stores metadata correctly."""
        metadata = {"author": "test", "version": 1}
        vfs.write("/test.txt", "Content", metadata=metadata)
        stored = vfs.get_metadata("/test.txt")
        assert stored == metadata

    def test_read_returns_none_for_missing(self, vfs: VFSManager) -> None:
        """Verify read returns None for missing files."""
        result = vfs.read("/nonexistent.txt")
        assert result is None

    def test_delete_existing_file(self, vfs: VFSManager) -> None:
        """Verify delete removes an existing file."""
        vfs.write("/test.txt", "Content")
        result = vfs.delete("/test.txt")
        assert result is True
        assert vfs.read("/test.txt") is None

    def test_delete_missing_file_returns_false(self, vfs: VFSManager) -> None:
        """Verify delete returns False for missing files."""
        result = vfs.delete("/nonexistent.txt")
        assert result is False

    def test_exists_returns_true_for_existing(self, vfs: VFSManager) -> None:
        """Verify exists returns True for existing files."""
        vfs.write("/test.txt", "Content")
        assert vfs.exists("/test.txt") is True

    def test_exists_returns_false_for_missing(self, vfs: VFSManager) -> None:
        """Verify exists returns False for missing files."""
        assert vfs.exists("/nonexistent.txt") is False

    def test_list_returns_matching_paths(self, vfs: VFSManager) -> None:
        """Verify list returns matching paths with prefix."""
        vfs.write("/dir/file1.txt", "Content1")
        vfs.write("/dir/file2.txt", "Content2")
        vfs.write("/other/file3.txt", "Content3")

        results = vfs.list("/dir")
        assert "/dir/file1.txt" in results
        assert "/dir/file2.txt" in results
        assert "/other/file3.txt" not in results


# Transaction tests
class TestTransactions:
    """Tests for transaction support."""

    def test_transaction_commits_on_success(self, vfs: VFSManager) -> None:
        """Verify transaction commits on successful completion."""
        with vfs.transaction():
            vfs.write("/trans1.txt", "Content1")
            vfs.write("/trans2.txt", "Content2")

        assert vfs.read("/trans1.txt") == "Content1"
        assert vfs.read("/trans2.txt") == "Content2"

    def test_transaction_rollbacks_on_exception(self, vfs: VFSManager) -> None:
        """Verify transaction rolls back on exception."""
        try:
            with vfs.transaction():
                vfs.write("/rollback1.txt", "Content1")
                raise ValueError("Test rollback")
        except ValueError:
            pass

        assert vfs.read("/rollback1.txt") is None

    def test_begin_commit_manual_transaction(self, vfs: VFSManager) -> None:
        """Verify manual begin/commit transaction."""
        vfs.begin()
        vfs.write("/manual.txt", "Content")
        vfs.commit()

        assert vfs.read("/manual.txt") == "Content"

    def test_rollback_reverts_changes(self, vfs: VFSManager) -> None:
        """Verify rollback reverts all changes."""
        vfs.begin()
        vfs.write("/rollback.txt", "Content")
        vfs.rollback()

        assert vfs.read("/rollback.txt") is None


# Metadata tests
class TestMetadata:
    """Tests for metadata operations."""

    def test_get_metadata_returns_stored_metadata(self, vfs: VFSManager) -> None:
        """Verify get_metadata returns stored metadata."""
        metadata = {"key": "value", "count": 42}
        vfs.write("/meta.txt", "Content", metadata=metadata)
        result = vfs.get_metadata("/meta.txt")
        assert result == metadata

    def test_get_metadata_returns_none_for_missing(self, vfs: VFSManager) -> None:
        """Verify get_metadata returns None for missing files."""
        result = vfs.get_metadata("/nonexistent.txt")
        assert result is None


# Stats tests
class TestStats:
    """Tests for statistics."""

    def test_get_stats_returns_correct_info(
        self, vfs: VFSManager, tmp_path: Path
    ) -> None:
        """Verify get_stats returns correct file count and db info."""
        vfs.write("/stats1.txt", "Content1")
        vfs.write("/stats2.txt", "Content2")

        stats = vfs.get_stats()
        assert stats["file_count"] == 2
        assert stats["db_path"] == str(tmp_path / "test_vfs.db")
        assert stats["db_size"] > 0
