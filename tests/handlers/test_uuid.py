"""Tests for UUID handler."""

import uuid as uuid_module

from agent_arsenal.handlers.uuid import _uuid7, handle_uuid


class TestHandleUuid:
    """Test cases for handle_uuid function."""

    def test_uuid4_basic(self):
        """Test basic UUID v4 generation."""
        result = handle_uuid(version=4)
        # UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        assert len(result) == 36
        assert result.count("-") == 4

    def test_uuid4_is_valid_uuid(self):
        """Test generated UUID v4 is valid."""
        result = handle_uuid(version=4)
        uuid_obj = uuid_module.UUID(result)
        assert uuid_obj.version == 4

    def test_uuid7_basic(self):
        """Test basic UUID v7 generation."""
        result = handle_uuid(version=7)
        assert len(result) == 36
        assert result.count("-") == 4

    def test_uuid7_is_valid_uuid(self):
        """Test generated UUID v7 is valid."""
        result = handle_uuid(version=7)
        uuid_obj = uuid_module.UUID(result)
        assert uuid_obj.version == 7

    def test_multiple_uuids(self):
        """Test generating multiple UUIDs."""
        result = handle_uuid(version=4, count=5)
        uuids = result.split("\n")
        assert len(uuids) == 5

    def test_count_one(self):
        """Test count of 1 returns single UUID."""
        result = handle_uuid(version=4, count=1)
        assert "\n" not in result

    def test_uppercase(self):
        """Test uppercase conversion."""
        result = handle_uuid(version=4, uppercase=True)
        assert result.isupper()

    def test_lowercase_default(self):
        """Test lowercase is default."""
        result = handle_uuid(version=4)
        assert result.islower() or result[0].islower()

    def test_invalid_version(self):
        """Test invalid version returns error."""
        result = handle_uuid(version=3)
        assert "Error" in result
        assert "version must be 4 or 7" in result

    def test_count_zero(self):
        """Test count of 0 returns error."""
        result = handle_uuid(version=4, count=0)
        assert "Error" in result
        assert "Count must be at least 1" in result

    def test_count_negative(self):
        """Test negative count returns error."""
        result = handle_uuid(version=4, count=-1)
        assert "Error" in result

    def test_count_too_large(self):
        """Test count exceeding 1000 returns error."""
        result = handle_uuid(version=4, count=1001)
        assert "Error" in result
        assert "cannot exceed 1000" in result

    def test_max_count(self):
        """Test max count of 1000 works."""
        result = handle_uuid(version=4, count=1000)
        uuids = result.split("\n")
        assert len(uuids) == 1000


class TestUuid7:
    """Test cases for _uuid7 function."""

    def test_uuid7_generates_string(self):
        """Test UUID v7 returns string."""
        result = _uuid7()
        assert isinstance(result, str)

    def test_uuid7_format(self):
        """Test UUID v7 has correct format."""
        result = _uuid7()
        assert len(result) == 36
        # Check version bits (should be 7)
        uuid_obj = uuid_module.UUID(result)
        assert uuid_obj.version == 7

    def test_uuid7_multiple_calls(self):
        """Test multiple UUID v7 calls produce unique values."""
        results = set()
        for _ in range(10):
            results.add(_uuid7())
        assert len(results) == 10  # All should be unique
