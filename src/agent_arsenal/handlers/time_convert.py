"""Time convert command handler."""

from datetime import datetime

from zoneinfo import ZoneInfo


def handle_time_convert(
    time: str = "",
    from_tz: str = "UTC",
    to_tz: str = "local",
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Convert time between timezones.

    Args:
        time: Time string to convert (default: now)
        from_tz: Source timezone
        to_tz: Target timezone
        format: Output format string

    Returns:
        Converted time
    """
    # Parse source timezone
    try:
        if from_tz == "local":
            from_zone = None
        else:
            from_zone = ZoneInfo(from_tz)
    except KeyError:
        return f"Error: Unknown source timezone '{from_tz}'. Use IANA timezone names like 'UTC', 'America/New_York'"
    
    # Parse target timezone
    try:
        if to_tz == "local":
            to_zone = None
        else:
            to_zone = ZoneInfo(to_tz)
    except KeyError:
        return f"Error: Unknown target timezone '{to_tz}'. Use IANA timezone names like 'UTC', 'America/New_York'"
    
    # Parse input time or use current time
    if time:
        # Try to parse the time string
        # First try as full datetime
        try:
            if from_zone:
                dt = datetime.fromisoformat(time).replace(tzinfo=from_zone)
            else:
                dt = datetime.fromisoformat(time)
        except ValueError:
            # Try strptime with common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%H:%M:%S",
                "%H:%M",
            ]
            
            dt = None
            for fmt in formats:
                try:
                    parsed = datetime.strptime(time, fmt)
                    if from_zone:
                        dt = parsed.replace(tzinfo=from_zone)
                    else:
                        dt = parsed
                    break
                except ValueError:
                    continue
            
            if dt is None:
                return f"Error: Could not parse time string '{time}'"
        
        # Ensure dt is not None before converting
        if dt is None:
            return f"Error: Could not parse time string '{time}'"
        
        # Convert to target timezone
        if to_zone:
            dt = dt.astimezone(to_zone)
        else:
            dt = dt.astimezone()  # Convert to local
        
    else:
        # Use current time
        if from_zone:
            dt = datetime.now(from_zone)
        else:
            dt = datetime.now()
        
        # Convert to target timezone
        if to_zone:
            dt = dt.astimezone(to_zone)
        else:
            dt = dt.astimezone()
    
    # Format output
    try:
        return dt.strftime(format)
    except ValueError as e:
        return f"Error: Invalid format string '{format}': {e}"