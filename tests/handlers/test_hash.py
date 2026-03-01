"""Tests for hash handler."""

from agent_arsenal.handlers.hash import handle_hash


class TestHandleHash:
    """Test cases for handle_hash function."""

    def test_sha256_basic(self):
        """Test basic SHA256 hashing."""
        result = handle_hash(algorithm="sha256", input="hello")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_md5_basic(self):
        """Test basic MD5 hashing."""
        result = handle_hash(algorithm="md5", input="hello")
        assert result == "5d41402abc4b2a76b9719d911017c592"

    def test_sha512_basic(self):
        """Test basic SHA512 hashing."""
        result = handle_hash(algorithm="sha512", input="hello")
        assert len(result) == 128  # SHA512 produces 64 hex chars * 2 = 128

    def test_empty_input(self):
        """Test empty input returns error."""
        result = handle_hash(algorithm="sha256", input="")
        assert result == "Error: No input provided"

    def test_no_input(self):
        """Test no input returns error."""
        result = handle_hash(algorithm="sha256")
        assert result == "Error: No input provided"

    def test_unknown_algorithm(self):
        """Test unknown algorithm returns error."""
        result = handle_hash(algorithm="sha999", input="test")
        assert "Error" in result
        assert "Unknown algorithm" in result

    def test_case_insensitive_algorithm(self):
        """Test algorithm is case insensitive."""
        result = handle_hash(algorithm="SHA256", input="test")
        assert result == handle_hash(algorithm="sha256", input="test")

    def test_encoding_utf8(self):
        """Test UTF-8 encoding."""
        result = handle_hash(algorithm="sha256", input="hello", encoding="utf-8")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_encoding_latin1(self):
        """Test Latin-1 encoding."""
        result = handle_hash(algorithm="sha256", input="hello", encoding="latin-1")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_encoding_hex(self):
        """Test hex encoding."""
        result = handle_hash(algorithm="sha256", input="68656c6c6f", encoding="hex")
        # "68656c6c6f" is "hello" in hex
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_encoding_base64(self):
        """Test base64 encoding."""
        result = handle_hash(algorithm="sha256", input="aGVsbG8=", encoding="base64")
        # "aGVsbG8=" is "hello" in base64
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_unknown_encoding(self):
        """Test unknown encoding returns error."""
        result = handle_hash(algorithm="sha256", input="test", encoding="invalid")
        assert "Error" in result
        assert "Unknown encoding" in result

    def test_invalid_hex_input(self):
        """Test invalid hex input returns error."""
        result = handle_hash(algorithm="sha256", input="nothex", encoding="hex")
        assert "Error" in result
        assert "Failed to decode" in result

    def test_invalid_base64_input(self):
        """Test invalid base64 input returns error."""
        # Use an invalid base64 string (has invalid characters for base64)
        result = handle_hash(algorithm="sha256", input="!!!invalid!!!", encoding="base64")
        assert "Error" in result
        assert "Failed to decode" in result

    def test_stdin_input(self):
        """Test reading from stdin with -."""
        import io
        import sys
        from unittest.mock import patch

        with patch.object(sys, "stdin", io.StringIO("hello")):
            result = handle_hash(algorithm="sha256", input="-")
            assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"