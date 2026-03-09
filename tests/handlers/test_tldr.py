"""Tests for tldr handler."""

import subprocess
from unittest.mock import patch

from agent_arsenal.handlers.tldr import (
    get_installation_instructions,
    get_tldr_client,
    handle_tldr,
    is_tldr_available,
)


class TestTldrHandler:
    """Test cases for tldr handler functions."""

    # Tests for is_tldr_available()

    def test_is_tldr_available_returns_true_when_tldr_in_path(self):
        """Test is_tldr_available returns True when tldr is in PATH."""
        with patch("agent_arsenal.handlers.tldr.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/tldr"
            result = is_tldr_available()
            assert result is True

    def test_is_tldr_available_returns_false_when_not_installed(self):
        """Test is_tldr_available returns False when no client installed."""
        with patch("agent_arsenal.handlers.tldr.shutil.which") as mock_which:
            mock_which.return_value = None
            result = is_tldr_available()
            assert result is False

    # Tests for get_tldr_client()

    def test_get_tldr_client_returns_first_available(self):
        """Test get_tldr_client returns first available client."""
        with patch("agent_arsenal.handlers.tldr.shutil.which") as mock_which:
            mock_which.side_effect = ["/usr/bin/tldr", None]
            result = get_tldr_client()
            assert result == "tldr"

    def test_get_tldr_client_returns_tlrc_when_tldr_not_available(self):
        """Test get_tldr_client returns tlrc when tldr not available."""
        with patch("agent_arsenal.handlers.tldr.shutil.which") as mock_which:
            mock_which.side_effect = [None, "/usr/bin/tlrc"]
            result = get_tldr_client()
            assert result == "tlrc"

    def test_get_tldr_client_returns_none_when_none_available(self):
        """Test get_tldr_client returns None when no client available."""
        with patch("agent_arsenal.handlers.tldr.shutil.which") as mock_which:
            mock_which.return_value = None
            result = get_tldr_client()
            assert result is None

    # Tests for get_installation_instructions()

    def test_get_installation_instructions_contains_pipx(self):
        """Test installation instructions contain pipx method."""
        result = get_installation_instructions()
        assert "pipx install tldr" in result

    def test_get_installation_instructions_contains_cargo(self):
        """Test installation instructions contain cargo method."""
        result = get_installation_instructions()
        assert "cargo install tlrc" in result

    def test_get_installation_instructions_contains_npm(self):
        """Test installation instructions contain npm method."""
        result = get_installation_instructions()
        assert "npm install -g tldr" in result

    def test_get_installation_instructions_contains_brew(self):
        """Test installation instructions contain brew method."""
        result = get_installation_instructions()
        assert "brew install tlrc" in result

    # Tests for handle_tldr()

    def test_handle_tldr_returns_installation_prompt_when_not_installed(self):
        """Test handle_tldr returns installation instructions when not installed."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = None
            result = handle_tldr("docker")
            assert "pipx install tldr" in result

    def test_handle_tldr_returns_page_when_successful(self):
        """Test handle_tldr returns tldr page on successful execution."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["tldr", "docker"],
                    returncode=0,
                    stdout="docker help content",
                    stderr="",
                )
                result = handle_tldr("docker")
                assert result == "docker help content"

    def test_handle_tldr_returns_not_found_when_command_missing(self):
        """Test handle_tldr returns not found when tldr returns 127."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["tldr", "nonexistent"],
                    returncode=127,
                    stdout="",
                    stderr="No tldr entry for nonexistent",
                )
                result = handle_tldr("nonexistent")
                assert "not found in tldr pages" in result

    def test_handle_tldr_returns_error_on_subprocess_failure(self):
        """Test handle_tldr returns error on non-zero non-127 returncode."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["tldr", "docker"],
                    returncode=1,
                    stdout="",
                    stderr="Some error occurred",
                )
                result = handle_tldr("docker")
                assert "Some error occurred" in result

    def test_handle_tldr_returns_timeout_message_on_timeout(self):
        """Test handle_tldr returns timeout message on timeout."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("tldr", 30)
                result = handle_tldr("docker")
                assert "timed out" in result

    def test_handle_tldr_returns_error_on_exception(self):
        """Test handle_tldr returns error on unexpected exception."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.side_effect = OSError("Something went wrong")
                result = handle_tldr("docker")
                assert "Error running tldr" in result
                assert "Something went wrong" in result

    def test_handle_tldr_strips_ansi_codes(self):
        """Test handle_tldr strips ANSI escape codes from output."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["tldr", "docker"],
                    returncode=0,
                    stdout="\x1b[32mdocker\x1b[0m help content",
                    stderr="",
                )
                result = handle_tldr("docker")
                assert result == "docker help content"

    def test_handle_tldr_strips_ansi_codes_from_error(self):
        """Test handle_tldr strips ANSI escape codes from error output."""
        with patch("agent_arsenal.handlers.tldr.get_tldr_client") as mock_client:
            mock_client.return_value = "tldr"
            with patch("agent_arsenal.handlers.tldr.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    args=["tldr", "docker"],
                    returncode=1,
                    stdout="",
                    stderr="\x1b[31mSome error\x1b[0m",
                )
                result = handle_tldr("docker")
                assert "Some error" in result
                assert "\x1b" not in result
