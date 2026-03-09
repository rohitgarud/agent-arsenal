"""Port check handler."""

import socket


def handle_port_check(port: int = 80, host: str = "localhost", timeout: int = 3) -> str:
    """Check if a network port is open.

    Args:
        port: Port number to check
        host: Host to check
        timeout: Connection timeout in seconds

    Returns:
        Port status message
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return f"Port {port} on {host} is OPEN"
        else:
            return f"Port {port} on {host} is CLOSED"
    except socket.gaierror:
        return f"Error: Could not resolve host '{host}'"
    except TimeoutError:
        return f"Port {port} on {host} is CLOSED (timeout)"
    except Exception as e:
        return f"Error: {e}"
