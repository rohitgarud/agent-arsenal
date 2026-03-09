"""Relative time handler."""
from datetime import datetime, timedelta


def get_relative_time(date: str, from_date: str = "") -> str:
    """Calculate relative time from now.

    Args:
        date: Date string (YYYY-MM-DD or ISO format)
        from_date: Reference date (defaults to now)

    Returns:
        Relative time string
    """
    if not date:
        return "Error: Date is required"

    try:
        # Parse the target date
        target = parse_date(date)
    except ValueError as e:
        return f"Error: Invalid date format: {e}"

    try:
        # Parse the reference date (default to now)
        if from_date:
            reference = parse_date(from_date)
        else:
            reference = datetime.now()
    except ValueError as e:
        return f"Error: Invalid from_date format: {e}"

    # Calculate difference
    delta = reference - target

    # Handle future dates
    if delta.total_seconds() < 0:
        return format_future_time(abs(delta))

    return format_past_time(delta)


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime

    Raises:
        ValueError: If date format is invalid
    """
    # Try various formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try dateutil-like parsing
    raise ValueError(f"Unable to parse date: {date_str}")


def format_past_time(delta: timedelta) -> str:
    """Format past timedelta as relative time.

    Args:
        delta: Time difference

    Returns:
        Formatted relative time string
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds} second(s) ago"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute(s) ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour(s) ago"
    elif total_seconds < 2592000:  # 30 days
        days = total_seconds // 86400
        return f"{days} day(s) ago"
    elif total_seconds < 31536000:  # 365 days
        months = total_seconds // 2592000
        return f"{months} month(s) ago"
    else:
        years = total_seconds // 31536000
        return f"{years} year(s) ago"


def format_future_time(delta: timedelta) -> str:
    """Format future timedelta as relative time.

    Args:
        delta: Time difference

    Returns:
        Formatted relative time string
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return f"in {total_seconds} second(s)"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"in {minutes} minute(s)"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"in {hours} hour(s)"
    elif total_seconds < 2592000:
        days = total_seconds // 86400
        return f"in {days} day(s)"
    elif total_seconds < 31536000:
        months = total_seconds // 2592000
        return f"in {months} month(s)"
    else:
        years = total_seconds // 31536000
        return f"in {years} year(s)"
