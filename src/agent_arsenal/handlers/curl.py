"""HTTP request handler."""
import json
from urllib import error, request


def http_request(url: str, method: str = "GET", data: str = "", headers: str = "") -> str:
    """Make HTTP request.

    Args:
        url: URL to request
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data
        headers: Custom headers as JSON string

    Returns:
        Response body or error message
    """
    if not url:
        return "Error: URL is required"

    try:
        # Prepare headers
        header_dict = {}
        if headers:
            try:
                header_dict = json.loads(headers)
            except json.JSONDecodeError:
                return "Error: Invalid headers JSON"

        # Prepare body
        body = None
        if data and method in ("POST", "PUT", "PATCH"):
            body = data.encode("utf-8")
            if "Content-Type" not in header_dict:
                header_dict["Content-Type"] = "application/json"

        # Build request
        req = request.Request(url, data=body, headers=header_dict, method=method)

        # Make request
        with request.urlopen(req, timeout=30) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")

            return f"Status: {status_code}\n\n{response_body}"

    except error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"
