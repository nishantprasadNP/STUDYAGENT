"""Time helpers. "Today" always means today in the student's timezone."""

from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones


@lru_cache(maxsize=1)
def _iana_names() -> frozenset[str]:
    return frozenset(available_timezones())


def is_valid_timezone(name: str) -> bool:
    """True only for canonical IANA names known to tzdata (case-sensitive)."""
    return name in _iana_names()


def today_in(tz: str) -> date:
    """The current calendar date in timezone `tz`."""
    return datetime.now(ZoneInfo(tz)).date()
