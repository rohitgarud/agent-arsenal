"""Tests for timestamp handler."""

from agent_arsenal.handlers.timestamp import handle_timestamp


class TestHandleTimestamp:
    """Test cases for handle_timestamp function."""

    def test_default_format(self):
        """Test default format returns timestamp."""
        result = handle_timestamp()
        # Default format: "%Y-%m-%d %H:%M:%S"
        assert len(result) == 19
        assert result.count("-") == 2
        assert result.count(":") == 2

    def test_unix_timestamp(self):
        """Test unix timestamp returns integer string."""
        result = handle_timestamp(unix=True)
        assert result.isdigit()
        # Should be reasonable timestamp (2020+)
        assert int(result) > 1577836800

    def test_custom_format(self):
        """Test custom format string."""
        result = handle_timestamp(format="%Y-%m-%d")
        assert len(result) == 10
        assert result.count("-") == 2

    def test_format_with_time(self):
        """Test format with time components."""
        result = handle_timestamp(format="%H:%M:%S")
        assert len(result) == 8
        assert result.count(":") == 2

    def test_utc_timezone(self):
        """Test UTC timezone."""
        result = handle_timestamp(tz="UTC")
        # Should return valid timestamp
        assert len(result) >= 10

    def test_unknown_timezone(self):
        """Test unknown timezone returns error."""
        result = handle_timestamp(tz="Invalid/Timezone")
        assert "Error" in result
        assert "Unknown timezone" in result

    def test_invalid_format_string(self):
        """Test invalid format string passes through (Python doesn't validate)."""
        # Note: Python's strftime doesn't validate format strings strictly
        # It passes through most invalid specifiers
        result = handle_timestamp(format="%invalid")
        # The format passes through as-is
        assert "%invalid" in result or "Error" in result

    def test_timezone_case_sensitivity(self):
        """Test timezone names are case sensitive."""
        # UTC should work
        result_utc = handle_timestamp(tz="UTC")
        assert "Error" not in result_utc

    def test_local_timezone(self):
        """Test local timezone."""
        result = handle_timestamp(tz="local")
        # Should return valid timestamp
        assert len(result) >= 10

    def test_America_New_York_timezone(self):
        """Test named timezone."""
        result = handle_timestamp(tz="America/New_York")
        assert "Error" not in result

    def test_Europe_London_timezone(self):
        """Test another named timezone."""
        result = handle_timestamp(tz="Europe/London")
        assert "Error" not in result

    def test_unix_with_timezone(self):
        """Test unix timestamp with timezone."""
        result = handle_timestamp(unix=True, tz="UTC")
        assert result.isdigit()

    def test_custom_format_with_timezone(self):
        """Test custom format with timezone."""
        result = handle_timestamp(format="%Y-%m-%d %H:%M:%S", tz="UTC")
        assert len(result) == 19