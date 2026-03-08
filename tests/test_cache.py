"""Unit tests for CacheManager."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_arsenal.cache import CacheEntry, CacheManager
from agent_arsenal.executor import CommandResult


@pytest.fixture
def temp_cache_dir(tmp_path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def cache_manager(temp_cache_dir) -> CacheManager:
    """Create a CacheManager instance with temp directory."""
    CacheManager.reset_instance()
    manager = CacheManager(cache_dir=temp_cache_dir, default_ttl=60)
    yield manager
    CacheManager.reset_instance()


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_to_command_result(self):
        """Test converting CacheEntry back to CommandResult."""
        entry = CacheEntry(
            key="abc123",
            command_path="/path/to/command.md",
            execution_type="python",
            args_hash="def456",
            result_success=True,
            result_output="Hello World",
            result_error=None,
            result_metadata={"key": "value"},
            created_at=datetime.now().isoformat(),
            ttl_seconds=3600,
            file_mtime=1234567890.0,
        )

        result = entry.to_command_result()

        assert result.success is True
        assert result.output == "Hello World"
        assert result.error is None
        assert result.metadata == {"key": "value"}

    def test_to_command_result_with_error(self):
        """Test converting CacheEntry with error back to CommandResult."""
        entry = CacheEntry(
            key="abc123",
            command_path="/path/to/command.md",
            execution_type="python",
            args_hash="def456",
            result_success=False,
            result_output="",
            result_error="Something went wrong",
            result_metadata={"error_code": 500},
            created_at=datetime.now().isoformat(),
            ttl_seconds=3600,
            file_mtime=1234567890.0,
        )

        result = entry.to_command_result()

        assert result.success is False
        assert result.output == ""
        assert result.error == "Something went wrong"
        assert result.metadata == {"error_code": 500}


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_singleton(self, temp_cache_dir):
        """Test that CacheManager is a singleton."""
        CacheManager.reset_instance()
        manager1 = CacheManager(cache_dir=temp_cache_dir)
        manager2 = CacheManager.get_instance()
        assert manager1 is manager2

    def test_singleton_returns_same_instance(self, temp_cache_dir):
        """Test that get_instance returns the same instance."""
        CacheManager.reset_instance()
        manager1 = CacheManager(cache_dir=temp_cache_dir)
        manager2 = CacheManager.get_instance()
        manager3 = CacheManager.get_instance()
        assert manager1 is manager2 is manager3

    def test_reset_instance(self, temp_cache_dir):
        """Test that reset_instance creates a new instance."""
        CacheManager.reset_instance()
        manager1 = CacheManager(cache_dir=temp_cache_dir)
        CacheManager.reset_instance()
        manager2 = CacheManager(cache_dir=temp_cache_dir)
        assert manager1 is not manager2

    def test_generate_key_deterministic(self, temp_cache_dir):
        """Test that generate_key produces consistent results."""
        CacheManager.reset_instance()
        manager = CacheManager(cache_dir=temp_cache_dir)

        path = Path("/test/command.md")
        args = {"host": "localhost", "port": 5432}

        key1 = manager.generate_key(path, args)
        key2 = manager.generate_key(path, args)

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    def test_generate_key_different_args(self, temp_cache_dir):
        """Test that different args produce different keys."""
        CacheManager.reset_instance()
        manager = CacheManager(cache_dir=temp_cache_dir)

        path = Path("/test/command.md")

        key1 = manager.generate_key(path, {"host": "localhost"})
        key2 = manager.generate_key(path, {"host": "other"})

        assert key1 != key2

    def test_generate_key_different_execution_type(self, temp_cache_dir):
        """Test that different execution types produce different keys."""
        CacheManager.reset_instance()
        manager = CacheManager(cache_dir=temp_cache_dir)

        path = Path("/test/command.md")
        args = {"host": "localhost"}

        key1 = manager.generate_key(path, args, execution_type="prompt")
        key2 = manager.generate_key(path, args, execution_type="python")

        assert key1 != key2

    def test_generate_key_different_path(self, temp_cache_dir):
        """Test that different paths produce different keys."""
        CacheManager.reset_instance()
        manager = CacheManager(cache_dir=temp_cache_dir)

        args = {"host": "localhost"}

        key1 = manager.generate_key(Path("/test/command1.md"), args)
        key2 = manager.generate_key(Path("/test/command2.md"), args)

        assert key1 != key2

    def test_set_and_get(self, cache_manager, tmp_path):
        """Test basic cache set and get."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test output")
        key = cache_manager.generate_key(command_path, {})

        cache_manager.set(key, result, ttl=60, command_path=command_path)

        cached = cache_manager.get(key, command_path)
        assert cached is not None
        assert cached.output == "test output"

    def test_cache_miss(self, cache_manager, tmp_path):
        """Test cache miss returns None."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        key = "nonexistent-key"
        cached = cache_manager.get(key, command_path)

        assert cached is None

    def test_cache_disabled(self, cache_manager, tmp_path):
        """Test that cache returns None when disabled."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        cache_manager.set_enabled(False)

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        cached = cache_manager.get(key, command_path)
        assert cached is None

    def test_cache_enabled_by_default(self, cache_manager):
        """Test that caching is enabled by default."""
        assert cache_manager.is_enabled() is True

    def test_set_enabled(self, cache_manager):
        """Test setting cache enabled state."""
        cache_manager.set_enabled(False)
        assert cache_manager.is_enabled() is False

        cache_manager.set_enabled(True)
        assert cache_manager.is_enabled() is True

    def test_ttl_expiry(self, cache_manager, tmp_path):
        """Test that expired entries are removed."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        # Create entry with 1 second TTL
        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, ttl=1, command_path=command_path)

        # Immediate get should work
        cached = cache_manager.get(key, command_path)
        assert cached is not None

        # Wait for expiry
        time.sleep(1.5)

        # Should now return None and remove entry
        cached = cache_manager.get(key, command_path)
        assert cached is None
        assert key not in cache_manager._cache

    def test_ttl_expiry_preserves_other_entries(self, cache_manager, tmp_path):
        """Test that TTL expiry only removes expired entries."""
        command_path1 = tmp_path / "test1.md"
        command_path1.write_text("# Test 1")
        command_path2 = tmp_path / "test2.md"
        command_path2.write_text("# Test 2")

        # Create entry with 1 second TTL
        result1 = CommandResult(success=True, output="test1")
        key1 = cache_manager.generate_key(command_path1, {})
        cache_manager.set(key1, result1, ttl=1, command_path=command_path1)

        # Create entry with long TTL
        result2 = CommandResult(success=True, output="test2")
        key2 = cache_manager.generate_key(command_path2, {})
        cache_manager.set(key2, result2, ttl=3600, command_path=command_path2)

        # Wait for first entry to expire
        time.sleep(1.5)

        # First should be None
        cached1 = cache_manager.get(key1, command_path1)
        assert cached1 is None

        # Second should still work
        cached2 = cache_manager.get(key2, command_path2)
        assert cached2 is not None
        assert cached2.output == "test2"

    def test_file_mtime_change_invalidates(self, cache_manager, tmp_path):
        """Test that file modification invalidates cache."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test v1")

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, ttl=3600, command_path=command_path)

        # Modify file (change mtime)
        time.sleep(0.1)
        command_path.write_text("# Test v2")

        # Cache should be invalidated
        cached = cache_manager.get(key, command_path)
        assert cached is None

    def test_file_not_exists_invalidates(self, cache_manager, tmp_path):
        """Test that missing file invalidates cache."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, ttl=3600, command_path=command_path)

        # Delete the file
        command_path.unlink()

        # Cache should be invalidated
        cached = cache_manager.get(key, command_path)
        assert cached is None

    def test_invalidate(self, cache_manager, tmp_path):
        """Test manual cache invalidation."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        # Invalidate
        assert cache_manager.invalidate(key) is True
        assert cache_manager.get(key, command_path) is None

        # Invalidate non-existent key
        assert cache_manager.invalidate("fake") is False

    def test_clear(self, cache_manager, tmp_path):
        """Test clearing all cache entries."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        count = cache_manager.clear()
        assert count == 1
        assert len(cache_manager._cache) == 0

    def test_clear_empty_cache(self, cache_manager):
        """Test clearing empty cache returns 0."""
        count = cache_manager.clear()
        assert count == 0

    def test_get_stats(self, cache_manager, tmp_path):
        """Test getting cache statistics."""
        stats = cache_manager.get_stats()

        assert "entry_count" in stats
        assert "enabled" in stats
        assert "default_ttl" in stats
        assert stats["enabled"] is True
        assert stats["default_ttl"] == 60
        assert stats["entry_count"] == 0

    def test_get_stats_with_entries(self, cache_manager, tmp_path):
        """Test stats reflect actual entries."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        stats = cache_manager.get_stats()
        assert stats["entry_count"] == 1

    def test_dont_cache_errors(self, cache_manager, tmp_path):
        """Test that error results are not cached."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        # Try to cache error result
        result = CommandResult(success=False, output="", error="Some error")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        # Should not be cached
        cached = cache_manager.get(key, command_path)
        assert cached is None
        assert key not in cache_manager._cache

    def test_dont_cache_errors_with_metadata(self, cache_manager, tmp_path):
        """Test that error results with metadata are not cached."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        # Try to cache error result with metadata
        result = CommandResult(
            success=False,
            output="",
            error="Some error",
            metadata={"error_code": 500}
        )
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, command_path=command_path)

        # Should not be cached
        cached = cache_manager.get(key, command_path)
        assert cached is None

    def test_persistence(self, cache_manager, tmp_path):
        """Test that cache persists to disk."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="persistent test")
        key = cache_manager.generate_key(command_path, {})
        cache_manager.set(key, result, ttl=3600, command_path=command_path)

        # Create new manager instance (simulates restart)
        CacheManager.reset_instance()
        new_manager = CacheManager(cache_dir=tmp_path / "cache")

        cached = new_manager.get(key, command_path)
        assert cached is not None
        assert cached.output == "persistent test"

    def test_persistence_with_different_default_ttl(self, temp_cache_dir, tmp_path):
        """Test persistence with different default TTL."""
        # Create manager with custom TTL
        CacheManager.reset_instance()
        manager1 = CacheManager(cache_dir=temp_cache_dir, default_ttl=120)

        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(success=True, output="test")
        key = manager1.generate_key(command_path, {})
        manager1.set(key, result, ttl=120, command_path=command_path)

        # Create new manager with same TTL
        CacheManager.reset_instance()
        manager2 = CacheManager(cache_dir=temp_cache_dir, default_ttl=120)

        cached = manager2.get(key, command_path)
        assert cached is not None
        assert cached.output == "test"

    def test_corrupt_cache_file(self, cache_manager, tmp_path):
        """Test handling of corrupt cache file."""
        cache_file = cache_manager.cache_file
        cache_file.write_text("{ invalid json }")

        # Should not raise, should start fresh
        CacheManager.reset_instance()
        new_manager = CacheManager(cache_dir=tmp_path / "cache")

        assert len(new_manager._cache) == 0

    def test_empty_cache_file(self, cache_manager, tmp_path):
        """Test handling of empty cache file."""
        cache_file = cache_manager.cache_file
        cache_file.write_text("")

        # Should not raise, should start fresh
        CacheManager.reset_instance()
        new_manager = CacheManager(cache_dir=tmp_path / "cache")

        assert len(new_manager._cache) == 0

    def test_missing_cache_file(self, cache_manager, tmp_path):
        """Test that missing cache file is handled gracefully."""
        cache_file = cache_manager.cache_file
        if cache_file.exists():
            cache_file.unlink()

        # Should not raise, should start with empty cache
        CacheManager.reset_instance()
        new_manager = CacheManager(cache_dir=tmp_path / "cache")

        assert len(new_manager._cache) == 0

    def test_default_ttl(self, temp_cache_dir):
        """Test default TTL value."""
        CacheManager.reset_instance()
        manager = CacheManager(cache_dir=temp_cache_dir, default_ttl=3600)
        assert manager.get_default_ttl() == 3600

    def test_set_default_ttl(self, cache_manager):
        """Test setting default TTL."""
        cache_manager.set_default_ttl(7200)
        assert cache_manager.get_default_ttl() == 7200

    def test_set_requires_command_path(self, cache_manager, tmp_path):
        """Test that set requires command_path."""
        result = CommandResult(success=True, output="test")
        key = "test-key"

        with pytest.raises(ValueError, match="command_path is required"):
            cache_manager.set(key, result, command_path=None)

    def test_caching_with_metadata(self, cache_manager, tmp_path):
        """Test caching results with metadata."""
        command_path = tmp_path / "test.md"
        command_path.write_text("# Test")

        result = CommandResult(
            success=True,
            output="test output",
            metadata={"execution_time": 1.5, "cache_hit": False}
        )
        key = cache_manager.generate_key(command_path, {})

        cache_manager.set(key, result, command_path=command_path)

        cached = cache_manager.get(key, command_path)
        assert cached is not None
        assert cached.metadata == {"execution_time": 1.5, "cache_hit": False}
