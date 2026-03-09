"""Tests for session state persistence across processes."""

import json
import os
import unittest.mock

import pytest

from agent_arsenal.state import ArsenalState, Scope


@pytest.fixture
def temp_state_dir(tmp_path):
    """Setup a temporary state directory."""
    state_dir = tmp_path / ".agent-arsenal"
    session_dir = state_dir / "sessions"
    session_dir.mkdir(parents=True)
    return state_dir


class TestSessionPersistence:
    """Tests for session persistence using PPID."""

    def test_session_sharing_same_ppid(self, temp_state_dir):
        """Verify that two instances with the same PPID share state."""
        ppid = 12345

        with (
            unittest.mock.patch("os.getppid", return_value=ppid),
            unittest.mock.patch("os.environ.get", return_value=None),
        ):
            # Instance 1: Set state
            state1 = ArsenalState()
            # Force re-init paths for test
            state1.state_dir = temp_state_dir
            state1.session_dir = temp_state_dir / "sessions"
            state1.session_id = state1._get_session_id()
            state1.session_file = state1._get_session_file_path(state1.session_id)

            state1.set("shared_key", "hello", Scope.SESSION)
            assert state1.session_id == f"ppid-{ppid}"
            assert state1.session_file.exists()

            # Instance 2: Should restore state
            # Since ArsenalState is a singleton, we need to clear or bypass it for a true 'fresh' test
            # or just test that restore_session works on a new object if we could bypass singleton.
            # Given singleton, we simulate a 'new' process by manually calling restore on the same instance
            # after mocking a file existence.

            state1._session_state = {}  # Manually clear memory
            state1.restore_session()
            assert state1.get("shared_key", Scope.SESSION) == "hello"

    def test_session_isolation_different_ppid(self, temp_state_dir):
        """Verify that instances with different PPIDs are isolated."""
        ppid1 = 11111
        ppid2 = 22222

        # Process 1
        with (
            unittest.mock.patch("os.getppid", return_value=ppid1),
            unittest.mock.patch("os.environ.get", return_value=None),
        ):
            state1 = ArsenalState()
            state1.state_dir = temp_state_dir
            state1.session_dir = temp_state_dir / "sessions"
            state1.session_id = state1._get_session_id()
            state1.session_file = state1._get_session_file_path(state1.session_id)
            state1.set("key1", "val1", Scope.SESSION)

        # Process 2
        with (
            unittest.mock.patch("os.getppid", return_value=ppid2),
            unittest.mock.patch("os.environ.get", return_value=None),
        ):
            # We must force session_id update because of singleton
            state1.session_id = state1._get_session_id()
            state1.session_file = state1._get_session_file_path(state1.session_id)
            state1._session_state = {}  # Clear memory
            state1.restore_session()

            assert state1.get("key1", Scope.SESSION) is None
            assert state1.session_id == f"ppid-{ppid2}"

    def test_cleanup_stale_sessions(self, temp_state_dir):
        """Verify that stale sessions (PID not running) are cleaned up."""
        # We use 'pid' in metadata but it now represents PPID.
        # cleanup_sessions checks if metadata['pid'] is running.

        stale_ppid = 999999
        active_ppid = os.getpid()  # Current process is definitely running

        stale_file = temp_state_dir / "sessions" / f"ppid-{stale_ppid}.json"
        active_file = temp_state_dir / "sessions" / f"ppid-{active_ppid}.json"

        stale_file.write_text(
            json.dumps(
                {
                    "metadata": {"pid": stale_ppid, "session_id": f"ppid-{stale_ppid}"},
                    "data": {},
                }
            )
        )
        active_file.write_text(
            json.dumps(
                {
                    "metadata": {
                        "pid": active_ppid,
                        "session_id": f"ppid-{active_ppid}",
                    },
                    "data": {},
                }
            )
        )

        state = ArsenalState()
        state.session_dir = temp_state_dir / "sessions"
        # Ensure our "active" file isn't the current session file of the singleton
        state.session_file = temp_state_dir / "sessions" / "some-other-session.json"

        with unittest.mock.patch.object(
            state, "_is_pid_running", side_effect=lambda p: p == active_ppid
        ):
            cleaned = state.cleanup_sessions()
            assert cleaned == 1
            assert not stale_file.exists()
            assert active_file.exists()
