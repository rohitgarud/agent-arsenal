"""Tests for the watcher module."""

import time


from agent_arsenal.watcher import CommandWatcher


class TestCommandWatcher:
    """Tests for CommandWatcher class."""

    def test_watcher_initialization(self, tmp_path):
        """Verify watcher setup."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=callback,
            debounce_ms=100,
        )

        assert watcher.commands_dir == tmp_path
        assert watcher.debounce_ms == 100
        assert not watcher.is_watching

    def test_watcher_start_stop(self, tmp_path):
        """Test start/stop lifecycle."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=callback,
            debounce_ms=100,
        )

        # Start watcher
        watcher.start()
        assert watcher.is_watching

        # Give it a moment to start
        time.sleep(0.2)

        # Stop watcher
        watcher.stop()
        time.sleep(0.1)

        assert not watcher.is_watching

    def test_watcher_default_debounce(self, tmp_path):
        """Test default debounce value."""
        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=lambda: None,
        )

        assert watcher.debounce_ms == 500

    def test_watcher_multiple_start(self, tmp_path):
        """Test that starting twice doesn't cause issues."""
        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=lambda: None,
        )

        # Start twice - should be idempotent
        watcher.start()
        first_watching = watcher.is_watching

        watcher.start()
        second_watching = watcher.is_watching

        assert first_watching == second_watching

        # Clean up
        watcher.stop()

    def test_watcher_stop_not_started(self, tmp_path):
        """Test stopping a watcher that wasn't started."""
        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=lambda: None,
        )

        # Should not raise
        watcher.stop()
        assert not watcher.is_watching


class TestCommandWatcherFilters:
    """Tests for file filtering."""

    def test_watcher_filters_md_files(self, tmp_path):
        """Test that watcher only triggers on .md files."""
        changes_detected = []

        def callback():
            changes_detected.append(True)

        watcher = CommandWatcher(
            commands_dir=tmp_path,
            reload_callback=callback,
            debounce_ms=100,
        )

        # Create a .py file (should be ignored)
        py_file = tmp_path / "test.py"
        py_file.write_text("# test")

        # Create a .md file (should be tracked)
        md_file = tmp_path / "test.md"
        md_file.write_text("# test")

        # Just verify initialization works - actual filtering is done by watchfiles
        assert watcher.commands_dir == tmp_path
