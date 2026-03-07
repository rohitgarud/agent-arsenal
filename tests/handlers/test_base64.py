"""Tests for base64 handler."""

from agent_arsenal.handlers.base64 import _wrap_text, handle_base64


class TestHandleBase64:
    """Test cases for handle_base64 function."""

    def test_encode_basic(self):
        """Test basic Base64 encoding."""
        result = handle_base64(subcommand="encode", input="Hello, World!")
        assert result == "SGVsbG8sIFdvcmxkIQ=="

    def test_encode_empty_input(self):
        """Test encoding with no input."""
        result = handle_base64(subcommand="encode", input="")
        assert result == "Error: No input provided"

    def test_encode_with_wrap(self):
        """Test encoding with wrap parameter."""
        result = handle_base64(subcommand="encode", input="Hello, World!", wrap=10)
        assert "\n" in result
        # Check that no line exceeds 10 chars
        for line in result.split("\n"):
            assert len(line) <= 10

    def test_encode_uppercase(self):
        """Test encoding produces ASCII output."""
        result = handle_base64(subcommand="encode", input="test")
        assert result.isascii()

    def test_decode_basic(self):
        """Test basic Base64 decoding."""
        result = handle_base64(subcommand="decode", input="SGVsbG8sIFdvcmxkIQ==")
        assert result == "Hello, World!"

    def test_decode_with_padding(self):
        """Test decoding with different padding."""
        result = handle_base64(subcommand="decode", input="YQ==")  # 'a' with padding
        assert result == "a"

    def test_decode_invalid_base64(self):
        """Test decoding invalid Base64."""
        result = handle_base64(subcommand="decode", input="not-valid-base64!!!")
        assert result.startswith("Error:")

    def test_decode_empty_input(self):
        """Test decoding empty input."""
        result = handle_base64(subcommand="decode", input="")
        assert result == ""

    def test_unknown_mode(self):
        """Test unknown mode returns error."""
        result = handle_base64(subcommand="invalid", input="test")
        assert "Error" in result
        assert "Unknown mode" in result

    def test_case_insensitive_mode(self):
        """Test mode is case insensitive."""
        result = handle_base64(subcommand="ENCODE", input="test")
        assert result == "dGVzdA=="

    def test_decode_whitespace_handling(self):
        """Test decoding removes whitespace."""
        result = handle_base64(subcommand="decode", input="  SGVsbG8=  ")
        assert result == "Hello"

    def test_encode_bytes_input(self):
        """Test encoding bytes input."""
        result = handle_base64(subcommand="encode", input=b"bytes")
        assert result == "Ynl0ZXM="

    def test_encode_with_stdin(self):
        """Test reading from stdin with -."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        with patch.object(sys, "stdin", StringIO("test")):
            result = handle_base64(subcommand="encode", input="-")
            assert result == "dGVzdA=="

    def test_decode_with_stdin(self):
        """Test reading from stdin for decode."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        with patch.object(sys, "stdin", StringIO("dGVzdA==")):
            result = handle_base64(subcommand="decode", input="-")
            assert result == "test"


class TestWrapText:
    """Test cases for _wrap_text function."""

    def test_wrap_basic(self):
        """Test basic text wrapping."""
        result = _wrap_text("abcdefghij", width=3)
        assert result == "abc\ndef\nghi\nj"

    def test_wrap_exact_width(self):
        """Test wrapping at exact width boundary."""
        result = _wrap_text("abcdef", width=3)
        assert result == "abc\ndef"

    def test_wrap_no_wrap_needed(self):
        """Test text shorter than width."""
        result = _wrap_text("ab", width=10)
        assert result == "ab"

    def test_wrap_zero_width(self):
        """Test zero width wraps every character."""
        result = _wrap_text("abc", width=1)
        assert result == "a\nb\nc"
