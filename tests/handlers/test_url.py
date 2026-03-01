"""Tests for URL handler."""

from agent_arsenal.handlers.url import handle_url


class TestHandleUrl:
    """Test cases for handle_url function."""

    def test_encode_basic(self):
        """Test basic URL encoding."""
        result = handle_url(mode="encode", input="hello world")
        assert result == "hello%20world"

    def test_encode_with_special_chars(self):
        """Test encoding special characters."""
        result = handle_url(mode="encode", input="hello?foo=bar&baz=qux")
        # Special chars should be URL-encoded
        assert "%3F" in result  # ? encoded
        assert "%3D" in result  # = encoded
        assert "%26" in result  # & encoded

    def test_encode_empty_input(self):
        """Test encoding with empty input."""
        result = handle_url(mode="encode", input="")
        assert result == "Error: No input provided"

    def test_decode_basic(self):
        """Test basic URL decoding."""
        result = handle_url(mode="decode", input="hello%20world")
        assert result == "hello world"

    def test_decode_with_special_chars(self):
        """Test decoding special characters."""
        result = handle_url(mode="decode", input="hello%3Ffoo%3Dbar")
        assert result == "hello?foo=bar"

    def test_decode_percent_encoding(self):
        """Test decoding percent-encoded characters."""
        result = handle_url(mode="decode", input="%3C%3E%22%27")
        assert result == '<>"\''

    def test_decode_empty_input(self):
        """Test decoding with empty input."""
        result = handle_url(mode="decode", input="")
        # Empty input triggers the "no input" check before decoding
        assert "Error" in result
        assert "No input provided" in result

    def test_unknown_mode(self):
        """Test unknown mode returns error."""
        result = handle_url(mode="invalid", input="test")
        assert "Error" in result
        assert "Unknown mode" in result

    def test_case_insensitive_mode(self):
        """Test mode is case insensitive."""
        result = handle_url(mode="ENCODE", input="test")
        assert result == handle_url(mode="encode", input="test")

    def test_encode_unicode(self):
        """Test encoding unicode characters."""
        result = handle_url(mode="encode", input="hello cafés")
        assert "%C3%A9" in result  # é is encoded as %C3%A9

    def test_decode_unicode(self):
        """Test decoding unicode characters."""
        result = handle_url(mode="decode", input="hello%20caf%C3%A9s")
        assert result == "hello cafés"

    def test_encode_path_like(self):
        """Test encoding path-like strings."""
        result = handle_url(mode="encode", input="/path/to/file")
        assert "/" in result  # Slashes should remain

    def test_error_handling(self):
        """Test error handling for edge cases."""
        # Passing None should not crash
        result = handle_url(mode="encode", input=None)
        # Should handle gracefully
        assert isinstance(result, str)