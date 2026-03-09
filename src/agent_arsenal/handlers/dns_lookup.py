"""DNS lookup handler."""
import socket


def dns_lookup(domain: str, record_type: str = "A") -> str:
    """Perform DNS lookup for a domain.

    Args:
        domain: Domain name to lookup
        record_type: DNS record type (A, AAAA, MX, TXT, CNAME, NS)

    Returns:
        DNS lookup results or error message
    """
    if not domain:
        return "Error: Domain is required"

    try:
        # Map record types to socket constants
        record_type_map = {
            "A": socket.AF_INET,  # IPv4
            "AAAA": socket.AF_INET6,  # IPv6
            "MX": socket.SOCK_STREAM,  # Used for MX
            "TXT": socket.SOCK_STREAM,
            "CNAME": socket.SOCK_STREAM,
            "NS": socket.SOCK_STREAM,
        }

        if record_type not in record_type_map:
            return f"Error: Unsupported record type: {record_type}. Supported: A, AAAA, MX, TXT, CNAME, NS"

        if record_type in ("A", "AAAA"):
            # Direct lookup for A/AAAA records
            results = socket.getaddrinfo(domain, None, record_type_map[record_type])
            unique_ips = list({r[4][0] for r in results})
            return f"{record_type} records for {domain}:\n" + "\n".join(f"  - {ip}" for ip in unique_ips)
        else:
            # Use socket.gethostbyname_ex for other types (simplified)
            try:
                result = socket.gethostbyname_ex(domain)
                return f"{record_type} for {domain}:\n  - {result[2][0]}"
            except socket.gaierror:
                # Fallback: try direct resolution
                ip = socket.gethostbyname(domain)
                return f"{record_type} for {domain}:\n  - {ip}"

    except socket.gaierror as e:
        return f"DNS lookup failed: {e}"
    except Exception as e:
        return f"Error: {e}"
