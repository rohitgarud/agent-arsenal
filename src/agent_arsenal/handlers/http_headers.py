"""HTTP headers handler."""

from urllib import error, request


def get_headers(url: str, follow_redirects: bool = True) -> str:
    """Fetch HTTP headers from a URL.

    Args:
        url: URL to fetch headers from
        follow_redirects: Whether to follow redirects

    Returns:
        HTTP headers or error message
    """
    if not url:
        return "Error: URL is required"

    try:
        # Build request
        req = request.Request(url, method="HEAD")

        # Handle redirects
        if not follow_redirects:
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        with request.urlopen(req, timeout=30) as response:
            headers = response.getheaders()
            status_code = response.status

            result = [f"Status: {status_code}", "", "Headers:"]
            for name, value in headers:
                result.append(f"  {name}: {value}")

            return "\n".join(result)

    except error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason}\n\nHeaders:\n" + "\n".join(
            f"  {k}: {v}" for k, v in e.headers.items()
        )
    except error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"
