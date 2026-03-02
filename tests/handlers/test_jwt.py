"""Tests for JWT handler."""

from agent_arsenal.handlers.jwt import handle_jwt


class TestHandleJwt:
    """Test cases for handle_jwt function."""

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        # A valid JWT token (header.payload.signature)
        # This is a test token with {"alg": "HS256", "typ": "JWT"} as header
        # and {"sub": "1234567890", "name": "John Doe", "iat": 1516239022} as payload
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = handle_jwt(token=token)
        assert "=== HEADER ===" in result
        assert "=== PAYLOAD ===" in result
        assert "alg" in result
        assert "HS256" in result

    def test_decode_header_only(self):
        """Test decoding only header."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result = handle_jwt(token=token, part="header")
        assert "=== HEADER ===" in result
        assert "=== PAYLOAD ===" not in result
        assert "=== SIGNATURE ===" not in result

    def test_decode_payload_only(self):
        """Test decoding only payload."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result = handle_jwt(token=token, part="payload")
        assert "=== HEADER ===" not in result
        assert "=== PAYLOAD ===" in result
        assert "=== SIGNATURE ===" not in result
        assert "1234567890" in result

    def test_decode_signature_only(self):
        """Test decoding only signature."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result = handle_jwt(token=token, part="signature")
        assert "=== HEADER ===" not in result
        assert "=== PAYLOAD ===" not in result
        assert "=== SIGNATURE ===" in result
        assert "not verified" in result

    def test_no_token(self):
        """Test empty token returns error."""
        result = handle_jwt(token="")
        assert "Error" in result
        assert "No token provided" in result

    def test_invalid_token_format(self):
        """Test invalid token format returns error."""
        # Use a token with wrong number of parts
        result = handle_jwt(token="only.two")
        assert "Error" in result
        assert "Invalid JWT format" in result

    def test_token_only_one_part(self):
        """Test token with only one part returns error."""
        result = handle_jwt(token="justonepart")
        assert "Error" in result

    def test_token_too_many_parts(self):
        """Test token with too many parts returns error."""
        result = handle_jwt(token="part1.part2.part3.extra")
        assert "Error" in result

    def test_invalid_header_base64(self):
        """Test invalid header base64 returns error."""
        result = handle_jwt(token="!!!invalidheader.part2.part3")
        assert "Error" in result
        assert "header" in result.lower()

    def test_invalid_payload_base64(self):
        """Test invalid payload base64 returns error."""
        result = handle_jwt(token="eyJhbGciOiJIUzI1NiJ9.!!!invalidpayload.part3")
        assert "Error" in result
        assert "payload" in result.lower()

    def test_case_insensitive_part(self):
        """Test part parameter is case insensitive."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result_upper = handle_jwt(token=token, part="HEADER")
        result_lower = handle_jwt(token=token, part="header")
        assert result_upper == result_lower

    def test_payload_json_formatting(self):
        """Test payload is formatted as JSON."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result = handle_jwt(token=token, part="payload")
        # Should have indented JSON
        assert "  " in result  # Indentation

    def test_all_parts_order(self):
        """Test 'all' part shows all sections in order."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.test"
        result = handle_jwt(token=token, part="all")
        header_pos = result.find("=== HEADER ===")
        payload_pos = result.find("=== PAYLOAD ===")
        sig_pos = result.find("=== SIGNATURE ===")
        assert header_pos < payload_pos < sig_pos
