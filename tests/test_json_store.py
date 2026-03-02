"""Tests for JSON store utility."""

import json
from pathlib import Path
from unittest.mock import patch

from agent_arsenal.utils.json_store import JSONStore


class TestJSONStore:
    """Test cases for JSONStore class."""

    def test_init(self, tmp_path):
        """Test initialization sets file path."""
        file_path = tmp_path / "test.json"
        store = JSONStore(file_path)
        assert store.file_path == file_path

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading nonexistent file returns empty dict."""
        file_path = tmp_path / "nonexistent.json"
        store = JSONStore(file_path)
        result = store.load()
        assert result == {}

    def test_load_existing_valid_json(self, tmp_path):
        """Test loading existing valid JSON file."""
        file_path = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        file_path.write_text(json.dumps(data))

        store = JSONStore(file_path)
        result = store.load()
        assert result == data

    def test_load_empty_file(self, tmp_path):
        """Test loading empty file returns empty dict."""
        file_path = tmp_path / "empty.json"
        file_path.write_text("")

        store = JSONStore(file_path)
        result = store.load()
        assert result == {}

    def test_load_whitespace_only_file(self, tmp_path):
        """Test loading file with only whitespace returns empty dict."""
        file_path = tmp_path / "whitespace.json"
        file_path.write_text("   \n\t  ")

        store = JSONStore(file_path)
        result = store.load()
        assert result == {}

    def test_load_invalid_json(self, tmp_path, caplog):
        """Test loading invalid JSON returns empty dict and logs warning."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")

        store = JSONStore(file_path)
        result = store.load()
        assert result == {}

    def test_save_creates_parent_dirs(self, tmp_path):
        """Test saving creates parent directories."""
        file_path = tmp_path / "nested" / "dir" / "test.json"
        store = JSONStore(file_path)
        store.save({"key": "value"})

        assert file_path.exists()
        assert file_path.parent.exists()

    def test_save_writes_valid_json(self, tmp_path):
        """Test saving writes valid JSON."""
        file_path = tmp_path / "test.json"
        store = JSONStore(file_path)
        data = {"key": "value", "number": 42, "nested": {"a": 1}}

        store.save(data)

        # Read back and verify
        loaded = json.loads(file_path.read_text())
        assert loaded == data

    def test_save_atomic_write(self, tmp_path):
        """Test save uses atomic write (temp file then rename)."""
        file_path = tmp_path / "test.json"
        store = JSONStore(file_path)
        data = {"test": "data"}

        store.save(data)

        # Verify the file was created and contains correct data
        assert file_path.exists()
        loaded = json.loads(file_path.read_text())
        assert loaded == data

    def test_save_overwrites_existing(self, tmp_path):
        """Test save overwrites existing file."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"old": "data"}')

        store = JSONStore(file_path)
        store.save({"new": "data"})

        loaded = json.loads(file_path.read_text())
        assert loaded == {"new": "data"}

    def test_exists_true(self, tmp_path):
        """Test exists returns True for existing file."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")

        store = JSONStore(file_path)
        assert store.exists() is True

    def test_exists_false(self, tmp_path):
        """Test exists returns False for nonexistent file."""
        file_path = tmp_path / "nonexistent.json"

        store = JSONStore(file_path)
        assert store.exists() is False

    def test_delete_existing_file(self, tmp_path):
        """Test deleting existing file returns True."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")

        store = JSONStore(file_path)
        result = store.delete()

        assert result is True
        assert not file_path.exists()

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file returns False."""
        file_path = tmp_path / "nonexistent.json"

        store = JSONStore(file_path)
        result = store.delete()

        assert result is False

    def test_delete_handles_io_error(self, tmp_path):
        """Test delete handles IO error gracefully."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")

        store = JSONStore(file_path)

        # Mock unlink to raise error
        with patch.object(Path, "unlink", side_effect=OSError("Delete failed")):
            result = store.delete()

        assert result is False

    def test_load_read_error(self, tmp_path, caplog):
        """Test load handles read errors gracefully."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{}")

        store = JSONStore(file_path)

        # Mock read_text to raise error
        with patch.object(Path, "read_text", side_effect=OSError("Read failed")):
            result = store.load()

        assert result == {}
