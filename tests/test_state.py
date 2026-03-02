"""Tests for the state module."""

import json

from agent_arsenal.state import ArsenalState, Scope, state


class TestArsenalState:
    """Tests for ArsenalState class."""

    def test_singleton(self):
        """Verify singleton pattern."""
        s1 = ArsenalState()
        s2 = ArsenalState()
        assert s1 is s2

    def test_state_singleton(self):
        """Verify global state instance is singleton."""
        s = state
        assert isinstance(s, ArsenalState)

    def test_get_set_session(self):
        """Test basic get/set for session scope."""
        # Use a fresh state for testing
        test_state = ArsenalState()
        test_state.clear()  # Clear any existing state

        # Set a value
        test_state.set("key1", "value1", Scope.SESSION)

        # Get the value
        result = test_state.get("key1", Scope.SESSION)
        assert result == "value1"

        # Get with default
        result = test_state.get("nonexistent", Scope.SESSION, "default")
        assert result == "default"

    def test_get_set_persistent(self):
        """Test basic get/set for persistent scope."""
        test_state = ArsenalState()
        test_state.clear(Scope.PERSISTENT)

        # Set a value
        test_state.set("key1", "value1", Scope.PERSISTENT)

        # Get the value
        result = test_state.get("key1", Scope.PERSISTENT)
        assert result == "value1"

    def test_delete(self):
        """Test delete operation."""
        test_state = ArsenalState()
        test_state.clear()

        # Set a value
        test_state.set("key1", "value1", Scope.SESSION)

        # Verify it exists
        assert test_state.get("key1", Scope.SESSION) == "value1"

        # Delete it
        deleted = test_state.delete("key1", Scope.SESSION)
        assert deleted is True

        # Verify it's gone
        assert test_state.get("key1", Scope.SESSION) is None

        # Delete nonexistent key should return False
        deleted = test_state.delete("nonexistent", Scope.SESSION)
        assert deleted is False

    def test_nested_keys(self):
        """Test dot notation for nested keys."""
        test_state = ArsenalState()
        test_state.clear()

        # Set nested value
        test_state.set("a.b.c", "nested_value", Scope.SESSION)

        # Get nested value
        result = test_state.get("a.b.c", Scope.SESSION)
        assert result == "nested_value"

        # Get parent should return dict
        result = test_state.get("a", Scope.SESSION)
        assert isinstance(result, dict)
        assert result["b"]["c"] == "nested_value"

    def test_nested_keys_set(self):
        """Test setting nested keys."""
        test_state = ArsenalState()
        test_state.clear()

        # Set nested value directly
        test_state.set("x.y.z", "deep", Scope.SESSION)

        result = test_state.get("x", Scope.SESSION)
        assert result["y"]["z"] == "deep"

    def test_persist(self, tmp_path):
        """Test persistence to disk."""
        test_state = ArsenalState()
        test_state.clear(Scope.PERSISTENT)

        # Set up temp state file
        test_state.state_dir = tmp_path
        test_state.state_file = tmp_path / "state.json"

        # Set values
        test_state.set("persist_key", "persist_value", Scope.PERSISTENT)
        test_state.set("nested.key", "nested_value", Scope.PERSISTENT)

        # Persist
        test_state.persist()

        # Verify file exists
        assert test_state.state_file.exists()

        # Verify content
        content = json.loads(test_state.state_file.read_text())
        assert content["persist_key"] == "persist_value"
        assert content["nested"]["key"] == "nested_value"

    def test_restore(self, tmp_path):
        """Test restoration from disk."""
        test_state = ArsenalState()
        test_state.clear(Scope.PERSISTENT)

        # Set up temp state file with content
        test_state.state_dir = tmp_path
        test_state.state_file = tmp_path / "state.json"

        # Write test data
        test_data = {"restore_key": "restore_value", "nested": {"key": "value"}}
        test_state.state_file.write_text(json.dumps(test_data))

        # Restore
        test_state.restore()

        # Verify restored values
        assert test_state.get("restore_key", Scope.PERSISTENT) == "restore_value"
        assert test_state.get("nested.key", Scope.PERSISTENT) == "value"

    def test_clear_scope(self):
        """Test clearing specific scope."""
        test_state = ArsenalState()
        test_state.clear()

        # Set values in different scopes
        test_state.set("session_key", "session_value", Scope.SESSION)
        test_state.set("persistent_key", "persistent_value", Scope.PERSISTENT)

        # Clear session only
        test_state.clear(Scope.SESSION)

        # Verify session is cleared
        assert test_state.get("session_key", Scope.SESSION) is None

        # Verify persistent still exists
        assert test_state.get("persistent_key", Scope.PERSISTENT) == "persistent_value"

    def test_clear_all(self):
        """Test clearing all scopes."""
        test_state = ArsenalState()
        test_state.clear()

        # Set values in all scopes
        test_state.set("session_key", "session_value", Scope.SESSION)
        test_state.set("persistent_key", "persistent_value", Scope.PERSISTENT)
        test_state.set("project_key", "project_value", Scope.PROJECT)

        # Clear all
        test_state.clear()

        # Verify all cleared
        assert test_state.get("session_key", Scope.SESSION) is None
        assert test_state.get("persistent_key", Scope.PERSISTENT) is None
        assert test_state.get("project_key", Scope.PROJECT) is None

    def test_project_scope(self, tmp_path):
        """Test project-level state."""
        test_state = ArsenalState()
        test_state.clear(Scope.PROJECT)

        # Create a temp project directory with .arsenal
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        arsenal_dir = project_dir / ".arsenal"
        arsenal_dir.mkdir()

        # Write project state
        project_state_file = arsenal_dir / "state.json"
        project_state_file.write_text(json.dumps({"project_key": "project_value"}))

        # Set project
        test_state.set_project(project_dir)

        # Verify project state loaded
        assert test_state.get("project_key", Scope.PROJECT) == "project_value"

    def test_list_keys(self):
        """Test listing keys in a scope."""
        test_state = ArsenalState()
        test_state.clear()

        # Set some values
        test_state.set("key1", "value1", Scope.SESSION)
        test_state.set("key2", "value2", Scope.SESSION)
        test_state.set("a.b", "nested", Scope.SESSION)

        # List keys
        keys = test_state.list_keys(Scope.SESSION)

        assert "key1" in keys
        assert "key2" in keys
        assert "a.b" in keys

    def test_thread_safety(self):
        """Test concurrent access to state."""
        import threading

        test_state = ArsenalState()
        test_state.clear()

        results = []

        def worker(thread_id):
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                test_state.set(key, f"value_{i}", Scope.SESSION)
                value = test_state.get(key, Scope.SESSION)
                results.append(value == f"value_{i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All operations should succeed
        assert all(results)


class TestScope:
    """Tests for Scope enum."""

    def test_scope_values(self):
        """Test scope enum values."""
        assert Scope.SESSION.value == "session"
        assert Scope.PERSISTENT.value == "persistent"
        assert Scope.PROJECT.value == "project"
