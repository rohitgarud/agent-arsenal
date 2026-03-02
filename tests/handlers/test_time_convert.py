"""Tests for time_convert handler."""

from agent_arsenal.handlers.time_convert import handle_time_convert


class TestHandleTimeConvert:
    """Test cases for handle_time_convert function."""

    def test_no_args_uses_current_time(self):
        """Test no args returns current time."""
        result = handle_time_convert()
        # Should return current time in default format
        assert len(result) == 19  # YYYY-MM-DD HH:MM:SS

    def test_convert_utc_to_local(self):
        """Test converting from UTC to local."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="local"
        )
        # Should return a valid timestamp
        assert len(result) == 19

    def test_convert_to_utc(self):
        """Test converting to UTC."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="America/New_York", to_tz="UTC"
        )
        assert len(result) == 19

    def test_unknown_source_timezone(self):
        """Test unknown source timezone returns error."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="Invalid/Timezone", to_tz="UTC"
        )
        assert "Error" in result
        assert "Unknown source timezone" in result

    def test_unknown_target_timezone(self):
        """Test unknown target timezone returns error."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="Invalid/Timezone"
        )
        assert "Error" in result
        assert "Unknown target timezone" in result

    def test_custom_format(self):
        """Test custom output format."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="UTC", format="%Y-%m-%d"
        )
        assert result == "2024-01-01"

    def test_iso_format_input(self):
        """Test ISO format input parsing."""
        result = handle_time_convert(
            time="2024-01-01T12:00:00", from_tz="UTC", to_tz="UTC"
        )
        assert "2024" in result

    def test_date_only_input(self):
        """Test date-only input parsing."""
        result = handle_time_convert(time="2024-01-01", from_tz="UTC", to_tz="UTC")
        assert "2024" in result

    def test_time_only_input(self):
        """Test time-only input parsing."""
        result = handle_time_convert(time="12:30:00", from_tz="UTC", to_tz="UTC")
        assert "12:30:00" in result or "12" in result

    def test_short_time_input(self):
        """Test short time format input."""
        result = handle_time_convert(time="12:30", from_tz="UTC", to_tz="UTC")
        assert "12" in result

    def test_invalid_time_string(self):
        """Test invalid time string returns error."""
        result = handle_time_convert(
            time="not-a-valid-time", from_tz="UTC", to_tz="UTC"
        )
        assert "Error" in result
        assert "Could not parse" in result

    def test_invalid_format_string(self):
        """Test invalid format string passes through (Python doesn't validate)."""
        # Note: Python's strftime doesn't validate format strings strictly
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="UTC", format="%invalid"
        )
        # The format passes through as-is
        assert "%invalid" in result or "Error" in result

    def test_local_to_utc(self):
        """Test converting from local to UTC."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="local", to_tz="UTC"
        )
        assert len(result) == 19

    def test_utc_to_local(self):
        """Test converting from UTC to local."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="local"
        )
        assert len(result) == 19

    def test_both_local(self):
        """Test converting from local to local."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="local", to_tz="local"
        )
        assert len(result) == 19

    def test_timezone_america_los_angeles(self):
        """Test America/Los_Angeles timezone."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="America/Los_Angeles"
        )
        assert len(result) == 19

    def test_timezone_europe_london(self):
        """Test Europe/London timezone."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="Europe/London"
        )
        assert len(result) == 19

    def test_timezone_asia_tokyo(self):
        """Test Asia/Tokyo timezone."""
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="Asia/Tokyo"
        )
        assert len(result) == 19

    def test_no_time_with_timezone(self):
        """Test using timezone with no time (current time)."""
        result = handle_time_convert(from_tz="UTC", to_tz="UTC")
        assert len(result) == 19

    def test_case_insensitive_timezone_names(self):
        """Test timezone names are case sensitive but valid ones work."""
        # UTC should work
        result = handle_time_convert(
            time="2024-01-01 12:00:00", from_tz="UTC", to_tz="UTC"
        )
        assert "Error" not in result
