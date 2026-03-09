"""Epoch converter handler."""

from datetime import UTC, datetime


def epoch_converter(value: str, to_epoch: bool = True, tz: str = "UTC") -> str:
    """Convert epoch timestamps to/from datetime.

    Args:
        value: Epoch timestamp or datetime string
        to_epoch: If True, convert datetime to epoch; if False, epoch to datetime
        tz: Timezone (UTC, local, or IANA timezone name)

    Returns:
        Converted value
    """
    if not value:
        return "Error: Value is required"

    try:
        if to_epoch:
            return convert_to_epoch(value, tz)
        else:
            return convert_from_epoch(value, tz)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


def convert_to_epoch(date_str: str, tz: str) -> str:
    """Convert datetime string to epoch.

    Args:
        date_str: Datetime string
        tz: Timezone

    Returns:
        Epoch timestamp as string

    Raises:
        ValueError: If conversion fails
    """
    dt = parse_datetime(date_str, tz)
    return str(int(dt.timestamp()))


def convert_from_epoch(epoch_str: str, tz: str) -> str:
    """Convert epoch to datetime string.

    Args:
        epoch_str: Epoch timestamp
        tz: Timezone

    Returns:
        Formatted datetime string

    Raises:
        ValueError: If conversion fails
    """
    epoch = int(epoch_str)

    # Handle both seconds and milliseconds
    if epoch > 1e11:  # Likely milliseconds
        epoch = int(epoch / 1000)

    if tz == "local":
        dt = datetime.fromtimestamp(epoch)
    elif tz == "UTC":
        dt = datetime.fromtimestamp(epoch, tz=UTC)
    else:
        # Try to get timezone offset (simplified)
        dt = datetime.fromtimestamp(epoch, tz=UTC)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(date_str: str, tz: str) -> datetime:
    """Parse datetime string.

    Args:
        date_str: Datetime string
        tz: Timezone

    Returns:
        Parsed datetime

    Raises:
        ValueError: If parsing fails
    """
    # Try various formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if tz == "UTC":
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue

    raise ValueError(f"Unable to parse datetime: {date_str}")
