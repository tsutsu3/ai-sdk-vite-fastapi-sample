import datetime


def now() -> str:
    """Get the current UTC time as an ISO formatted string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def now_str() -> str:
    return now()


def now_datetime() -> datetime.datetime:
    """Get the current UTC time as a datetime object."""
    return datetime.datetime.now(datetime.timezone.utc)
