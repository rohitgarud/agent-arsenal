"""Timestamp command handler."""

from datetime import datetime
from zoneinfo import ZoneInfo


def handle_timestamp(
    format: str = "%Y-%m-%d %H:%M:%S",
    tz: str = "local",
    unix: bool = False,
) -> str:
    """Get the current timestamp.

    Args:
        format: strftime format string
        tz: Timezone name (e.g., "UTC", "America/New_York", "local")
        unix: If True, return Unix timestamp

    Returns:
        Formatted timestamp string
    """
    # Determine timezone
    if tz == "local":
        dt = datetime.now()
    else:
        try:
            dt = datetime.now(ZoneInfo(tz))
        except KeyError:
            return f"Error: Unknown timezone '{tz}'. Use IANA timezone names like 'UTC', 'America/New_York', 'Europe/London'."

    # Return Unix timestamp if requested
    if unix:
        return str(int(dt.timestamp()))

    # Return formatted timestamp
    try:
        return dt.strftime(format)
    except ValueError as e:
        return f"Error: Invalid format string '{format}': {e}"
