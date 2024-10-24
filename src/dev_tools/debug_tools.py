"""
debug_tools.py

This module provides utilities for debugging and timing, including functions to check if debugging
or timing is enabled
and to log exceptions.
"""

import os
from enum import Enum


def is_debug_on() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.getenv("DEBUG", "False").lower() in ["true", "1", "t", "yes"]


def is_timing_on() -> bool:
    """Check if timing mode is enabled via environment variable."""
    return os.getenv("TIMING", "False").lower() in ["true", "1", "t", "yes"]


class TimePeriod(Enum):
    """
    An enumeration representing various time periods with their corresponding singular and plural
    names, durations in seconds, and whether they support decimal representation.

    Attributes:
        ACT_YEAR (tuple): Represents an actual year (365.25 days).
        YEAR (tuple): Represents a year (365 days).
        DAY (tuple): Represents a day.
        HOUR (tuple): Represents an hour.
        MINUTE (tuple): Represents a minute.
        SECOND (tuple): Represents a second.
    """

    ACT_YEAR = (" year", " years", 31557600, False)
    YEAR = (" year", " years", 365 * 60 * 60 * 24, False)
    DAY = (" day", " days", 60 * 60 * 24, False)
    HOUR = ("h", "h", 60 * 60, False)
    MINUTE = ("m", "m", 60, False)
    SECOND = ("s", "s", 1, True)

    @property
    def single_name(self) -> str:
        """Returns the singular name."""
        return self.value[0]

    @property
    def multiple_name(self) -> str:
        """Returns the plural name."""
        return self.value[1]

    @property
    def seconds(self) -> int:
        """Returns the duration in seconds."""
        return self.value[2]

    @property
    def has_decimals(self) -> bool:
        """Indicates if decimals are supported."""
        return self.value[3]


def human_readable_time(seconds: int) -> str:
    """
    Convert a number of seconds into a human-readable string with periods going up to a year.

    Args:
        seconds (int): The number of seconds to convert.

    Returns:
        str: Human-readable string representing the time elapsed.
    """
    periods: list[TimePeriod] = [
        TimePeriod.ACT_YEAR,
        TimePeriod.YEAR,
        TimePeriod.DAY,
        TimePeriod.HOUR,
        TimePeriod.MINUTE,
        TimePeriod.SECOND,
    ]

    time_str = []
    skip_year = False
    for period in periods:
        if skip_year and period == TimePeriod.YEAR:
            continue
        if seconds >= period.seconds:
            period_value, seconds = divmod(seconds, period.seconds)
            if period == TimePeriod.ACT_YEAR and period_value > 0:
                skip_year = True
            if period.has_decimals:
                time_str.append(f"{period_value+seconds:.3f}{period.single_name}")
            else:
                time_str.append(
                    (
                        f"{int(period_value)}"
                        f"{period.multiple_name if period_value != 1 else period.single_name}"
                    )
                )

    return " ".join(time_str) if time_str else "0.000s"
